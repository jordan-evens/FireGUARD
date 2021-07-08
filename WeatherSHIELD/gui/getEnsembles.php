<?php
require 'connection.php';


function setStart($offSet){
    $theStart = new DateTime('now');
    date_add($theStart, date_interval_create_from_date_string($offSet. " days"));
    return $theStart;
}


// round to this many digits because otherwise it's overkill
$lat = floatval($_GET['lat']);
$long = floatval($_GET['long']);
$offset = intval($_GET['dateOffset']);
$startDate = setStart($offset);
$numDays = strval($_GET['numDays']);

function modelArray($last_row, $membersArray)
{
    if(is_null($last_row['generated']))
    {
        echo('No historic match data exists');
        exit();
    }
    return array(
            // these are all Zulu times
            "Generated" => $last_row['generated'],
            "lat"=>floatval($last_row['latitude']),
            "lon"=>floatval($last_row['longitude']),
            // this is in meters, so no decimal digits should be fine
            "DistanceFrom" => round($last_row['distance_from']),
            "Members" => $membersArray
        );
}

function roundValue($value)
{
    // NOTE: idn't work with this as a global variable (rounded to 0 digits)
    $num_digits = 2;
    return round($value, $num_digits);
}

function getStartup($conn_dfoss, $offset, $lat, $long)
{
    return array(
        'Station' => null,
        'Generated' => null,
        'lat' => null,
        'lon' => null,
        'DistanceFrom' => null,
        'FFMC' => 0,
        'DMC' => 0,
        'DC' => 0,
        'APCP_0800' => 0,
    );
}

function readModels($conn, $sql, $indices, &$dates_array)
{
    $stmt = try_query($conn,$sql);
    $modelsArray = array();
    $last_model = null;
    $last_member = null;
    $last_generated = null;
    $last_row = null;
    $last_key = null;
    $is_same = null;
    while( $row = pg_fetch_array($stmt) ) {
        $cur_model = $row['model'];
        $cur_member = $row['member'];
        $temp = array();
        // output all the indices that we said we're going to provide
        foreach ($indices as $var) {
            array_push($temp, roundValue($row[$var]));
        }
        $is_same = $last_member == $cur_member && $last_model == $cur_model;
        // either new member or model
        if ($last_member != $cur_member || $last_model != $cur_model) {
            if (!is_null($last_row)) {
                $membersArray[$last_member] = $dataArray;
            }
            $dataArray = array();
            $last_member = $cur_member;
            
            // push all members into model array if new model
            if ($last_model != $cur_model) {
                if (!is_null($last_model)) {
                    $modelsArray[$last_model] = modelArray($last_row, $membersArray);
                }
                
                $membersArray = array();
                $last_model = $cur_model;
            }
        }
        $cur_date = $row['fortime'].' GMT';
        // use a single array of dates and then the index in that array for the members
        if (!in_array($cur_date, $dates_array)) {
            array_push($dates_array, $cur_date);
        }
        $date_key = array_search($cur_date, $dates_array);
        // if ($is_same && $last_key != ($date_key - 1))
        // {
            //HACK: output is missing a day so just duplicate
            // $dataArray[$date_key - 1] = $temp;
        // }
        $last_key = $date_key;
        $dataArray[$date_key] = $temp;
        $last_row = $row;
    }
    if (!is_null($last_member)) {
        $membersArray[$last_member] = $dataArray;
    }
    if (!is_null($last_model)) {
        $modelsArray[$last_model] = modelArray($last_row, $membersArray);
    }
    return $modelsArray;
}

$WX_DATABASE = 'FireGUARD';

$conn = connect($WX_DATABASE);
# use dfoss database from startDate
$conn_dfoss = connect('FireGUARD');
$conn_hindcast = connect('FireGUARD');
if ($conn && $conn_hindcast){
    // could probably look at only asking for what we're going to display
    $indices = array(
        'tmp',
        'rh',
        'ws',
        'wd',
        'apcp'
    );
    // if we've specified indices then only get those
    if (isset($_GET["indices"])) {
        $indices = array_map('strtolower', explode(',', strval($_GET['indices'])));
    }
    $outputArray = array();
    $outputArray['givenStart'] = $startDate->format('Y-m-d');
    $outputArray['FromDatabase'] = $WX_DATABASE;
    $outputArray['FakeDatabase'] = 'WX_'.date_format($startDate, 'Ym');
    // define which indices are going to be included and their order
    $outputArray['Indices'] = array_map('strtoupper', $indices);
    $outputArray['StartupValues'] = getStartup($conn_dfoss, $offset, $lat, $long);
    $dates_array = array();

    $sql = "SELECT *"
        //~ . " FROM INPUTS.FCT_Forecast(".$lat.", ".$long.", ".$numDays.")"
        . " FROM INPUTS.FCT_Forecast_By_Offset(".$offset.", ".$lat.", ".$long.", ".$numDays.")"
        . "  order by model, member, fortime";
    $outputArray['qry_FCT_Forecast'] = $sql;
    $outputArray['Models'] = readModels($conn, $sql, $indices, $dates_array);
    // don't do anything with the hindcasts if not > 15 days because they're empty
    if ($numDays > 15) {
        $matches = array();
        $grades = array();
        $sql_match = "SELECT year, avg_value, grade"
            . " FROM HINDCAST.FCT_HistoricMatch_By_Offset(".$offset.")"
            . " ORDER BY grade DESC";
        $outputArray['qry_FCT_HistoricMatch_By_Offset'] = $sql_match;
        $stmt = try_query($conn_hindcast,$sql_match);
        while( $row = pg_fetch_array($stmt) ) {
            array_push($matches, intval($row['year']));
            // HACK: enforce a minimum score
            // only displays 2 decimal places but log scale so need more precision
            $grades[$row['year']] = round(max($row['grade'], 0.0001), 4);
        }
        $outputArray['Matches'] = array('Order' => $matches, 'Grades' => $grades);
    }
    // NOTE: Needs to be included even if no historic matches since it's used for day 1 - 15 climate
    // NOTE: this automatically clips to 365 days in FCT_Hindcast
    // FIX: there's an issue with leap years not selecting Feb 29
    $sql = "SELECT *"
        . " FROM HINDCAST.FCT_Hindcast_By_Offset(".$offset.", ".$lat.", ".$long.", ".$numDays.")"
        . " order by model, member, fortime";
    $outputArray['qry_FCT_Hindcast_By_Offset'] = $sql;
    $outputArray['Hindcast'] = readModels($conn_hindcast, $sql, $indices, $dates_array);
    
    $outputArray['Actuals'] = array();
    
    $outputArray['ForDates'] = $dates_array;
    // we only need to know the day we started since they're sequential
    $outputArray['StartDate'] = $dates_array[0];
    echo json_encode($outputArray);
}
else{
    echo("Error could not connect to SQL database: ".print_r( pg_errors(), true));
}

/* Close the connection. */
pg_close( $conn);
pg_close( $conn_dfoss);
pg_close( $conn_hindcast);
?>