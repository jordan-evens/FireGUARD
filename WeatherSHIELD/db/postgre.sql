-- Database: FireGUARD

-- DROP DATABASE "FireGUARD";

CREATE DATABASE "FireGUARD"
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

COMMENT ON DATABASE "FireGUARD"
    IS 'weather and other information';

\c FireGUARD

-- Enable PostGIS (as of 3.0 contains just geometry/geography)
CREATE EXTENSION postgis;
-- enable raster support (for 3+)
CREATE EXTENSION postgis_raster;
-- Enable Topology
CREATE EXTENSION postgis_topology;
-- Enable PostGIS Advanced 3D
-- and other geoprocessing algorithms
-- sfcgal not available with all distributions
CREATE EXTENSION postgis_sfcgal;
-- fuzzy matching needed for Tiger
CREATE EXTENSION fuzzystrmatch;
-- rule based standardizer
CREATE EXTENSION address_standardizer;
-- example rule data set
CREATE EXTENSION address_standardizer_data_us;
-- Enable US Tiger Geocoder
CREATE EXTENSION postgis_tiger_geocoder;

-- Role: wx_readwrite
-- DROP ROLE wx_readwrite;

CREATE ROLE wx_readwrite WITH
  LOGIN
  NOSUPERUSER
  INHERIT
  NOCREATEDB
  NOCREATEROLE
  NOREPLICATION
  ENCRYPTED PASSWORD 'SCRAM-SHA-256$4096:c1HhyYundCPitcw/oyudAw==$iVpDx5uqq/FnyBT5d/QNYkI/zTp1X84i0AO0+8HH0jE=:5bR40MWo54ekMhp3F6B1FoSI/Uot5ZLtIQqxhfyAXqk=';
 
 -- Role: wx_readonly
-- DROP ROLE wx_readonly;

CREATE ROLE wx_readonly WITH
  LOGIN
  NOSUPERUSER
  INHERIT
  NOCREATEDB
  NOCREATEROLE
  NOREPLICATION
  ENCRYPTED PASSWORD 'SCRAM-SHA-256$4096:/vNJcJxZqMJgwjfSY6SlqQ==$SnJeXe3KYPusRCrHXeOTAWruW1CFbtEqNeFbxYAUPMo=:6lh+JWzI67I1svEbPsI9wSvxbOxGychScuRXLE6SNGE=';

CREATE SCHEMA INPUTS;
 
CREATE OR REPLACE FUNCTION INPUTS.DISTANCE
(
    LatitudeA FLOAT,
    LongitudeA FLOAT,
    LatitudeB FLOAT,
    LongitudeB FLOAT
)
RETURNS FLOAT AS $$
	BEGIN
		return ST_Distance(ST_SetSRID( ST_Point(LongitudeA, LatitudeA), 4326)::geography,
						   ST_SetSRID( ST_Point(LongitudeB, LatitudeB), 4326)::geography);
	END;
$$ LANGUAGE plpgsql;

CREATE TABLE INPUTS.DAT_Exclude_Points(
    Latitude float NOT NULL,
    Longitude float NOT NULL,
    CONSTRAINT PK_DatExcludePoints PRIMARY KEY(Latitude, Longitude)
);


-- add in all the points that are in lakes
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (42, -87);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (42, -83);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (42, -82);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (42, -81);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (43, -87);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (44, -87);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (44, -82);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (44, -77);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (45, -87);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (45, -86);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (45, -83);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (45, -82);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (45, -81);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (45, -80);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (46, -85);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (46, -83);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (46, -82);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (47, -91);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (47, -90);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (47, -89);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (47, -88);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (47, -87);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (47, -86);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (47, -85);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (48, -89);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (48, -88);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (48, -87);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (48, -86);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (49, -95);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (52, -80);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (52, -79);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (53, -80);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (53, -79);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (54, -82);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (54, -81);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (54, -80);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (54, -79);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (55, -82);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (55, -81);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (55, -80);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (55, -79);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (55, -73);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56, -87);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56, -86);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56, -85);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56, -84);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56, -83);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56, -82);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56, -81);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56, -80);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56, -78);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56, -77);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56, -74);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (57, -89);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (57, -88);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (57, -87);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (57, -86);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (57, -85);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (57, -84);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (57, -83);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (57, -82);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (57, -81);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (57, -80);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (57, -79);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (57, -78);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (57, -77);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (58, -92);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (58, -91);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (58, -90);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (58, -89);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (58, -88);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (58, -87);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (58, -86);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (58, -85);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (58, -84);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (58, -83);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (58, -82);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (58, -81);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (58, -80);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (58, -79);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (58, -78);

-- insert reanalysis lake points
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (42.856399536132812, -86.25);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (44.761100769042969, -86.25);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (44.761100769042969, -82.5);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (44.761100769042969, -80.625);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (46.665798187255859, -86.25);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (48.570499420166016, -88.125);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (52.379901885986328, -80.625);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (52.379901885986328, -78.75);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (54.284599304199219, -80.625);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56.189300537109375, -86.25);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56.189300537109375, -84.375);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56.189300537109375, -82.5);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56.189300537109375, -80.625);
INSERT INTO INPUTS.DAT_Exclude_Points(Latitude, Longitude) VALUES (56.189300537109375, -76.875);



CREATE TABLE INPUTS.DAT_Location(
    LocationId INT GENERATED ALWAYS AS IDENTITY,
    Latitude FLOAT NOT NULL,
    Longitude FLOAT NOT NULL,
    
    CONSTRAINT PK_DatLocation PRIMARY KEY(LocationId),
    CONSTRAINT UN_DatLocation UNIQUE (
        Latitude, Longitude
    )
);

ALTER TABLE INPUTS.DAT_Location
CLUSTER ON UN_DatLocation;

CREATE TABLE INPUTS.DAT_Model(
    ModelGeneratedId INT GENERATED ALWAYS AS IDENTITY,
    Model VARCHAR(20) NOT NULL,
    Generated TIMESTAMP NOT NULL,
    StartDate TIMESTAMP NOT NULL,
    
    CONSTRAINT PK_DatModel PRIMARY KEY(ModelGeneratedId),
    CONSTRAINT UN_DatModel UNIQUE (
        Generated, Model
    )
);

ALTER TABLE INPUTS.DAT_Model
CLUSTER ON UN_DatModel;

CREATE TABLE INPUTS.DAT_LocationModel(
    LocationModelId INT GENERATED ALWAYS AS IDENTITY,
    ModelGeneratedId INT NOT NULL,
    LocationId INT NOT NULL,
    
    CONSTRAINT PK_DatLocationModel PRIMARY KEY(LocationModelId),
    CONSTRAINT UN_DatLocationModel UNIQUE (
        ModelGeneratedId, LocationId
    ),
    CONSTRAINT FK_DatLocationModelM FOREIGN KEY (ModelGeneratedId) REFERENCES INPUTS.DAT_Model(ModelGeneratedId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
    ,
    CONSTRAINT FK_DatLocationModelL FOREIGN KEY (LocationId) REFERENCES INPUTS.DAT_Location(LocationId)
);

ALTER TABLE INPUTS.DAT_LocationModel
CLUSTER ON UN_DatLocationModel;

CREATE TABLE INPUTS.DAT_Forecast(
        LocationModelId INT NOT NULL,
        ForTime TIMESTAMP NOT NULL,
        Member INT NOT NULL,
        TMP FLOAT NOT NULL,
        RH FLOAT NOT NULL,
        WS FLOAT NOT NULL,
        WD FLOAT NOT NULL,
        APCP FLOAT NOT NULL,
        
        CONSTRAINT PK_DatForecast PRIMARY KEY (
            LocationModelId, ForTime, Member
        ),
        CONSTRAINT FK_DAT_Forecast FOREIGN KEY (LocationModelId) REFERENCES INPUTS.DAT_LocationModel(LocationModelId)
            ON DELETE CASCADE
            ON UPDATE CASCADE
);

ALTER TABLE INPUTS.DAT_Forecast
CLUSTER ON PK_DatForecast;

CREATE OR REPLACE FUNCTION INPUTS.FCT_Forecast_By_Offset (
    DateOffset INT,
    lat FLOAT,
    long FLOAT,
    NumberDays INT
)
RETURNS TABLE (
	Generated TIMESTAMP,
    ForTime TIMESTAMP,
	Model VARCHAR(20),
	Member INT,
	Latitude FLOAT,
	Longitude FLOAT,
    TMP FLOAT,
    RH FLOAT,
    WS FLOAT,
    WD FLOAT,
    APCP FLOAT,
	DISTANCE_FROM FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
	RETURN QUERY
    SELECT *
    FROM
    (
        SELECT
            dist.Generated,
            cur.ForTime,
            dist.Model,
            cur.Member,
            dist.Latitude,
            dist.Longitude, 
            cur.TMP,
            cur.RH,
            cur.WS,
            cur.WD,
            cur.APCP,
            dist.DISTANCE_FROM
        FROM
        (
            SELECT
                DISTINCT c.*
            FROM (SELECT m.Model, MAX(m.Generated) As Generated
                    FROM INPUTS.DAT_Model m
                    WHERE StartDate < (current_date + (DateOffset + 1) * INTERVAL '1 day')
                    GROUP BY m.Model) m
            INNER JOIN LATERAL (
                SELECT
                *
                FROM (
                    SELECT loc.Latitude,
                            loc.Longitude,
                            m.Generated,
                            m.Model,
                            lm.LocationModelId,
                            INPUTS.DISTANCE(loc.Latitude, loc.Longitude, lat, long) AS DISTANCE_FROM
                    FROM
                    (SELECT ModelGeneratedId
                    FROM INPUTS.DAT_Model d
                    WHERE d.Model=m.Model AND d.Generated=m.Generated) m2
                    LEFT JOIN INPUTS.DAT_LocationModel lm ON m2.ModelGeneratedId=lm.ModelGeneratedId
                    LEFT JOIN INPUTS.DAT_Location loc ON loc.LocationId=lm.LocationId
                    WHERE
                        -- We should always be in a reasonable boundary if we're looking +/- 1 degree around it
                        loc.Latitude >= (lat - 1) AND loc.Longitude >= (long - 1)
                        AND loc.Latitude <= (lat + 1) AND loc.Longitude <= (long + 1)
                        AND NOT EXISTS (SELECT * FROM INPUTS.DAT_Exclude_Points exc
                                    WHERE exc.Latitude=loc.Latitude AND exc.Longitude=loc.Longitude)
                ) s
                ORDER BY DISTANCE_FROM ASC
				LIMIT 1
            ) c ON true
        ) dist
        LEFT JOIN (SELECT *
                    FROM INPUTS.DAT_Forecast f
                    WHERE
                        f.ForTime <= (current_date + (DateOffset + NumberDays + 1) * INTERVAL '1 day')
                        AND f.ForTime >= (current_date + (DateOffset + 1) * INTERVAL '1 day')) cur ON
                    dist.LocationModelId=cur.LocationModelId
        ) n
        WHERE n.ForTime IS NOT NULL;
END; $$;


CREATE FUNCTION INPUTS.FCT_Forecast (
    lat FLOAT,
    long FLOAT,
    NumberDays INT
)
RETURNS TABLE (
	Generated TIMESTAMP,
    ForTime TIMESTAMP,
	Model VARCHAR(20),
	Member INT,
	Latitude FLOAT,
	Longitude FLOAT,
    TMP FLOAT,
    RH FLOAT,
    WS FLOAT,
    WD FLOAT,
    APCP FLOAT,
	DISTANCE_FROM FLOAT
)LANGUAGE plpgsql
AS $$
BEGIN
	RETURN QUERY
    SELECT * FROM INPUTS.FCT_Forecast_By_Offset(0, lat, long, NumberDays);
END; $$;

-- ***************************************************
--                    END OF INPUTS
-- ***************************************************

CREATE SCHEMA HINDCAST;

CREATE TABLE HINDCAST.DAT_Historic(
    HistoricGeneratedId INT GENERATED ALWAYS AS IDENTITY,
    Generated TIMESTAMP NOT NULL,
    
    CONSTRAINT PK_DatHistoric PRIMARY KEY(HistoricGeneratedId),
	CONSTRAINT UN_DatHistoric UNIQUE (Generated)
);

ALTER TABLE HINDCAST.DAT_Historic
CLUSTER ON UN_DatHistoric;

CREATE TABLE HINDCAST.DAT_HistoricMatch(
    HistoricGeneratedId INT NOT NULL,
    Year INT NOT NULL,
    Month INT NOT NULL,
    Value FLOAT NOT NULL,
    
    CONSTRAINT PK_DatHistoricMatch PRIMARY KEY (HistoricGeneratedId, Year, Month),
    CONSTRAINT FK_DatHistoricMatch FOREIGN KEY (HistoricGeneratedId) REFERENCES HINDCAST.DAT_Historic(HistoricGeneratedId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

ALTER TABLE HINDCAST.DAT_HistoricMatch
CLUSTER ON PK_DatHistoricMatch;
 
CREATE TABLE HINDCAST.DAT_Location(
    LocationId INT GENERATED ALWAYS AS IDENTITY,
    Latitude FLOAT NOT NULL,
    Longitude FLOAT NOT NULL,
    
    CONSTRAINT PK_HistDatLocation PRIMARY KEY(LocationId),
    CONSTRAINT UN_HistDatLocation UNIQUE (
        Latitude, Longitude
    )
);

ALTER TABLE HINDCAST.DAT_Location
CLUSTER ON UN_HistDatLocation;

CREATE TABLE HINDCAST.DAT_Model(
    ModelGeneratedId INT GENERATED ALWAYS AS IDENTITY,
    Model VARCHAR(20) NOT NULL,
    -- use Year instead of Generated because it actually affects performance quite a bit
    Year INT NOT NULL,
    
    CONSTRAINT PK_HistDatModel PRIMARY KEY(ModelGeneratedId),
    CONSTRAINT UN_HistDatModel UNIQUE (
        Year, Model
    )
);

ALTER TABLE HINDCAST.DAT_Model
CLUSTER ON UN_HistDatModel;

CREATE TABLE HINDCAST.DAT_LocationModel(
    LocationModelId INT GENERATED ALWAYS AS IDENTITY,
    ModelGeneratedId INT NOT NULL,
    LocationId INT NOT NULL,
    
    CONSTRAINT PK_HistDatLocationModel PRIMARY KEY(LocationModelId),
    CONSTRAINT UN_HistDatLocationModel UNIQUE (
        ModelGeneratedId, LocationId
    ),
    CONSTRAINT FK_HistDatLocationModelM FOREIGN KEY (ModelGeneratedId) REFERENCES HINDCAST.DAT_Model(ModelGeneratedId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
    ,
    CONSTRAINT FK_HistDatLocationModelL FOREIGN KEY (LocationId) REFERENCES HINDCAST.DAT_Location(LocationId)
);

ALTER TABLE HINDCAST.DAT_LocationModel
CLUSTER ON UN_HistDatLocationModel;

CREATE TABLE HINDCAST.DAT_Hindcast(
    LocationModelId INT NOT NULL,
    ForTime TIMESTAMP NOT NULL,
    TMP FLOAT NOT NULL,
    RH FLOAT NOT NULL,
    WS FLOAT NOT NULL,
    WD FLOAT NOT NULL,
    APCP FLOAT NOT NULL,
    APCP_0800 FLOAT NOT NULL,
    
    CONSTRAINT PK_HistDatHindcast PRIMARY KEY (
        LocationModelId, ForTime
    ),
    CONSTRAINT FK_HistDatHindcast FOREIGN KEY (LocationModelId) REFERENCES HINDCAST.DAT_LocationModel(LocationModelId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

ALTER TABLE HINDCAST.DAT_Hindcast
CLUSTER ON PK_HistDatHindcast;


-- ***************************************************
--                    END OF TABLES
-- ***************************************************

CREATE OR REPLACE FUNCTION HINDCAST.FCT_Historic_By_Date(
    FirstDay TIMESTAMP
)
RETURNS TABLE(
	Generated TIMESTAMP,
	Year INT,
	Month INT,
	Value FLOAT,
	FAKE_DATE TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
	RETURN QUERY
	SELECT
		h.Generated,
		m.Year,
		m.Month,
		m.Value,
		TIMESTAMP '1900-01-01' + ((m.Year - 1900) * INTERVAL '1 year') + ((m.Month - 1) * INTERVAL '1 month') AS FAKE_DATE
	FROM 
		(SELECT hist.Generated, hist.HistoricGeneratedId
			FROM HINDCAST.DAT_Historic hist
			WHERE hist.Generated <= FirstDay
			ORDER BY hist.Generated DESC
			LIMIT 1) h
		LEFT JOIN HINDCAST.DAT_HistoricMatch m ON h.HistoricGeneratedId=m.HistoricGeneratedId;
END;$$;

CREATE OR REPLACE FUNCTION HINDCAST.FCT_Closest (
    lat FLOAT,
    long FLOAT
)
RETURNS TABLE(
	LocationID INT,
	Latitude FLOAT,
	Longitude FLOAT,
	DISTANCE_FROM FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
	RETURN QUERY
    SELECT *
    FROM (
        SELECT loc.LocationId, loc.Latitude, loc.Longitude, INPUTS.DISTANCE(loc.Latitude, loc.Longitude, lat, long) AS DISTANCE_FROM
        FROM HINDCAST.DAT_Location loc
        WHERE
            NOT EXISTS (SELECT * FROM INPUTS.DAT_Exclude_Points exc
                        WHERE exc.Latitude=loc.Latitude AND exc.Longitude=loc.Longitude)
            -- We should always be in a reasonable boundary if we're looking +/- 3 degrees around it
            -- since resolution is 2.5 degrees
            AND loc.Latitude >= (lat - 3) AND loc.Longitude >= (long - 3)
            AND loc.Latitude <= (lat + 3) AND loc.Longitude <= (long + 3)
    ) s
    ORDER BY DISTANCE_FROM ASC
	LIMIT 1;
END;$$;

CREATE OR REPLACE FUNCTION HINDCAST.FCT_All_Closest (
    FirstDay TIMESTAMP,
    lat FLOAT,
    long FLOAT
)
RETURNS TABLE (
	Model VARCHAR(20),
	Latitude FLOAT,
	Longitude FLOAT,
	Generated TIMESTAMP,
	LocationModelId INT,
    ForTime TIMESTAMP,
    TMP FLOAT,
    RH FLOAT,
    WS FLOAT,
    WD FLOAT,
    APCP FLOAT,
    APCP_0800 FLOAT,
	FAKE_DATE TIMESTAMP,
	DISTANCE_FROM FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
	RETURN QUERY
    SELECT
        m.Model,
        c.Latitude,
        c.Longitude,
        (SELECT MAX(hist.Generated)
            FROM HINDCAST.DAT_Historic hist
            WHERE DATE(hist.Generated) <= FirstDay) as Generated,
        cur.*,
		(cur.ForTime + ((EXTRACT(YEAR from FirstDay) - EXTRACT(YEAR from cur.ForTime)) * INTERVAL '1 year')) AS FAKE_DATE,
        c.DISTANCE_FROM
    FROM
        HINDCAST.FCT_Closest(lat, long) c
        LEFT JOIN HINDCAST.DAT_LocationModel lm ON lm.LocationId=c.LocationId
        LEFT JOIN HINDCAST.DAT_Model m ON m.ModelGeneratedId=lm.ModelGeneratedId
        LEFT JOIN HINDCAST.DAT_Hindcast cur ON lm.LocationModelId=cur.LocationModelId;
END;$$;

CREATE OR REPLACE FUNCTION HINDCAST.FCT_Quadtratic
(
    Value FLOAT,
    alpha FLOAT,
    beta FLOAT,
    charlie FLOAT,
    delta FLOAT,
    epsilon FLOAT
)
RETURNS FLOAT
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN alpha * POWER(Value, 4) + beta * POWER(Value, 3) + charlie * POWER(Value, 2) + delta * Value + epsilon;
END;$$;

CREATE OR REPLACE FUNCTION HINDCAST.FCT_WeightMonth
(
    Month int
)
RETURNS FLOAT
LANGUAGE plpgsql
AS $$
	DECLARE a FLOAT := -1.7;
	DECLARE b FLOAT := 30;
	DECLARE c FLOAT := -146;
	DECLARE d FLOAT := 201;
	DECLARE e FLOAT := 140;
	DECLARE result FLOAT;
BEGIN
	result := HINDCAST.FCT_Quadtratic(Month, a, b, c, d, e);
	RETURN result;
END; $$;

CREATE FUNCTION HINDCAST.FCT_WeightMatch
(
    Value FLOAT
)
RETURNS FLOAT
LANGUAGE plpgsql
AS $$
    DECLARE a FLOAT := 0;
    DECLARE b FLOAT := 140;
    DECLARE c FLOAT := -341;
    DECLARE d FLOAT := 277;
    DECLARE e FLOAT := -75;
	DECLARE result FLOAT;
BEGIN
	result := HINDCAST.FCT_Quadtratic(Value, a, b, c, d, e);
    RETURN result;
END; $$;


CREATE FUNCTION HINDCAST.FCT_GradeHistoric
(
    Value FLOAT,
    Month INT
)
RETURNS FLOAT
LANGUAGE plpgsql
AS $$
	DECLARE result FLOAT;
BEGIN
    result := HINDCAST.FCT_WeightMonth(Month) * HINDCAST.FCT_WeightMatch(Value);
	RETURN result;
END; $$;


CREATE OR REPLACE FUNCTION HINDCAST.FCT_HistoricMatch_By_Offset
(
    DateOffset INT
)
RETURNS TABLE (
            Generated TIMESTAMP,
            Year INT,
            AVG_VALUE FLOAT,
            GRADE FLOAT
        )
LANGUAGE plpgsql
AS $$
    DECLARE FirstDay TIMESTAMP := (current_date + (DateOffset + 1) * INTERVAL '1 day');
    DECLARE NumberMonths INT := 5;
    DECLARE OffsetMonths INT := 0;
    DECLARE MinRatioScore FLOAT := 0.725;
BEGIN
    RETURN QUERY
    SELECT
        h.Generated,
        h.Year,
        AVG(s.Value) AS AVG_VALUE,
        -- needs to equal 1 when score is perfect
        (SUM(MONTH_GRADE) - SUM(HINDCAST.FCT_GradeHistoric(MinRatioScore, WHICH_MONTH)))/(SUM(HINDCAST.FCT_GradeHistoric(1, WHICH_MONTH)) - SUM(HINDCAST.FCT_GradeHistoric(MinRatioScore, WHICH_MONTH))) AS GRADE
    FROM
    (
        SELECT DISTINCT m.Year
        FROM HINDCAST.DAT_Model m
        WHERE m.YEAR < EXTRACT(YEAR from FirstDay)
    ) m
    INNER JOIN LATERAL
    (
        SELECT *
        FROM HINDCAST.FCT_Historic_By_Date(FirstDay) h
        WHERE h.Year=m.Year
    ) h ON true 
    INNER JOIN LATERAL
    (
        SELECT
            (h.FAKE_DATE + OffsetMonths * INTERVAL '1 month') AS START_FROM,
            HINDCAST.FCT_GradeHistoric(Value, (EXTRACT(MONTH from FAKE_DATE) + OffsetMonths)::integer) AS MONTH_GRADE,
            Value,
            (EXTRACT(MONTH from h.FAKE_DATE) + OffsetMonths)::integer AS WHICH_MONTH,
            FAKE_DATE as FOR_MONTH
        FROM HINDCAST.FCT_Historic_By_Date(FirstDay)
        WHERE
            FAKE_DATE >= h.FAKE_DATE + OffsetMonths * INTERVAL '1 month'
            -- not <= because that would be NumberMonths + 1 months
            AND FAKE_DATE < (h.FAKE_DATE + (NumberMonths + OffsetMonths) * INTERVAL '1 month')
    ) s ON true 
    WHERE EXTRACT(MONTH from h.FAKE_DATE)=EXTRACT(MONTH from FirstDay)
    GROUP BY h.Generated, h.Year, s.START_FROM;
END; $$;


CREATE OR REPLACE FUNCTION HINDCAST.FCT_HistoricMatch()
RETURNS TABLE (
	Generated TIMESTAMP,
	Year INT,
	AVG_VALUE FLOAT,
	GRADE FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
	RETURN QUERY
    SELECT * FROM HINDCAST.FCT_HistoricMatch_By_Offset(0);
END; $$;


CREATE OR REPLACE FUNCTION HINDCAST.FCT_Hindcast_Slice (
    FirstDay TIMESTAMP,
    lat FLOAT,
    long FLOAT,
    StartDay TIMESTAMP,
    NumberDays INT,
    YearOffset INT
)
RETURNS TABLE (
	Generated TIMESTAMP,
	ForTime TIMESTAMP,
	Model VARCHAR(20),
	Member INT,
	Latitude FLOAT,
	Longitude FLOAT,
	TMP FLOAT,
	RH FLOAT,
	WS FLOAT,
	WD FLOAT,
	APCP FLOAT,
	DISTANCE_FROM FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
	RETURN QUERY
	SELECT
    c.Generated,
    (c.FAKE_DATE + YearOffset * INTERVAL '1 year') AS ForTime,
    c.Model,
    (EXTRACT(YEAR from c.ForTime) - YearOffset)::integer as Member,
    c.Latitude,
    c.Longitude,
    c.TMP,
    c.RH,
    c.WS,
    c.WD,
    -- HACK: change to use 0800 - 1300 precip portion for day 1
    (SELECT CAST (
                CASE
                    WHEN DATE(c.FAKE_DATE)=DATE(FirstDay)
                        THEN (c.APCP - c.APCP_0800)
                    ELSE c.APCP
                END AS FLOAT)) as APCP,
    c.DISTANCE_FROM
FROM HINDCAST.FCT_ALL_Closest(FirstDay, lat, long) c
WHERE (FAKE_DATE + YearOffset * INTERVAL '1 year') > StartDay
-- HACK: do this instead of EndDay because some years have Feb 29 and so have more days
AND (c.FAKE_DATE + YearOffset * INTERVAL '1 year') < (StartDay + NumberDays * INTERVAL '1 day');
END; $$;


CREATE OR REPLACE FUNCTION HINDCAST.FCT_Hindcast_By_Offset (
    DateOffset INT,
    lat FLOAT,
    long FLOAT,
    NumberDays INT
)
RETURNS TABLE (
    Generated TIMESTAMP,
    ForTime TIMESTAMP,
    Model VARCHAR(20),
    Member INT,
    Latitude FLOAT,
    Longitude FLOAT,
    TMP FLOAT,
    RH FLOAT,
    WS FLOAT,
    WD FLOAT,
    APCP FLOAT,
    DISTANCE_FROM FLOAT
)
AS $$
    DECLARE CurrentEnd INT;
    DECLARE CurrentStart TIMESTAMP;
    DECLARE YearEnd TIMESTAMP;
    DECLARE MaxDays INT;
    DECLARE FirstDay TIMESTAMP := current_date + DateOffset * INTERVAL '1 day';
    DECLARE CurrentOffset INT := 0;
    DECLARE DaysPicked INT := 0;
BEGIN
	YearEnd := make_date(EXTRACT(YEAR from FirstDay)::integer + 1, 1, 1);
	CurrentStart := FirstDay;
	MaxDays := DATE_PART('day', YearEnd - CurrentStart);
    -- hard code a limit here because we don't want to duplicate data output
    IF NumberDays > 365 THEN
        NumberDays := 365;
	END IF;
    WHILE NumberDays > DaysPicked AND DaysPicked < 365 LOOP
        IF NumberDays < DaysPicked + MaxDays THEN
            CurrentEnd := (NumberDays - DaysPicked);
        ELSE
            CurrentEnd := MaxDays;
		END IF;
        DaysPicked := DaysPicked + CurrentEnd;
		RETURN QUERY
        SELECT
            *
        FROM HINDCAST.FCT_Hindcast_Slice(FirstDay, lat, long, CurrentStart, CurrentEnd, CurrentOffset) s
        WHERE s.Member IN (SELECT YEAR FROM HINDCAST.DAT_Model);
        CurrentOffset := CurrentOffset + 1;
        -- NOTE: this is until Jan 1  00:00:00 since we pick dates <= it and we need 18z of Dec 31
        CurrentStart := make_date(EXTRACT(YEAR from FirstDay)::integer + CurrentOffset, 1, 1);
        MaxDays := 365;
    END LOOP;
	RETURN;
END; $$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION HINDCAST.FCT_Hindcast (
    lat FLOAT,
    long FLOAT,
    NumberDays INT
)
RETURNS TABLE (
    Generated TIMESTAMP,
    ForTime TIMESTAMP,
    Model VARCHAR(20),
    Member INT,
    Latitude FLOAT,
    Longitude FLOAT,
    TMP FLOAT,
    RH FLOAT,
    WS FLOAT,
    WD FLOAT,
    APCP FLOAT,
    DISTANCE_FROM FLOAT
)
AS $$
BEGIN
	RETURN QUERY
    SELECT * FROM HINDCAST.FCT_Hindcast_By_Offset(0, lat, long, NumberDays);
END; $$ LANGUAGE plpgsql;



-- ***************************************************
--                    END OF HINDCAST
-- ***************************************************


GRANT USAGE ON SCHEMA INPUTS to wx_readwrite;
GRANT USAGE ON SCHEMA INPUTS to wx_readonly;
GRANT SELECT, INSERT, DELETE, UPDATE ON ALL TABLES IN SCHEMA INPUTS TO wx_readwrite;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA INPUTS TO wx_readwrite;
GRANT SELECT ON ALL TABLES IN SCHEMA INPUTS TO wx_readonly;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA INPUTS TO wx_readonly;

GRANT USAGE ON SCHEMA HINDCAST to wx_readwrite;
GRANT USAGE ON SCHEMA HINDCAST to wx_readonly;
GRANT SELECT, INSERT, DELETE, UPDATE ON ALL TABLES IN SCHEMA HINDCAST TO wx_readwrite;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA HINDCAST TO wx_readwrite;
GRANT SELECT ON ALL TABLES IN SCHEMA HINDCAST TO wx_readonly;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA HINDCAST TO wx_readonly;
