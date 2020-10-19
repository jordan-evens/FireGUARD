

IF OBJECT_ID('[HINDCAST].[FCT_Hindcast_Slice]') IS NOT NULL
    DROP FUNCTION [HINDCAST].[FCT_Hindcast_Slice];
GO
CREATE FUNCTION [HINDCAST].[FCT_Hindcast_Slice] (
    @Latitude AS float,
    @Longitude AS float,
    @StartDay AS int,
    @EndDay AS int,
    @YearOffset AS int
)
RETURNS TABLE
AS
RETURN
(
SELECT
    --~ DATEADD(dd, DATEDIFF(dd, 0, GETDATE()), @StartDay) AS [StartDay],
    --~ DATEADD(DD, DATEDIFF(DD, 0, GETDATE()), @EndDay) AS [EndDay],
    -- HACK: use max generated time from DAT_Historic since it should be the year we matched on
    (SELECT MAX([Generated])
        FROM [HINDCAST].[DAT_Historic]) AS [Generated],
    DATEADD(YY, @YearOffset, [FAKE_DATE]) AS [ForTime],
    [Model],
    (YEAR([ForTime]) - @YearOffset) as [Member],
    [Latitude],
    [Longitude],
    [TMP],
    [RH],
    [WS],
    [WD],
    -- HACK: change to use 0800 - 1300 precip portion for day 1
    (SELECT CAST (
                CASE
                    WHEN 0 = DATEDIFF(dd, [FAKE_DATE], GETDATE())
                        THEN ([APCP] - [APCP_0800])
                    ELSE [APCP]
                END AS float)) as [APCP],
    [DISTANCE_FROM]
FROM [HINDCAST].[HINDCAST].[FCT_ALL_Closest](@Latitude, @Longitude) c
-- stick with 15 days because we know that's what it should be and we want to see any gaps
--WHERE [FAKE_DATE] > DATEADD(dd, @StartDay, DATEDIFF(dd, 0, GETDATE()))
--AND [FAKE_DATE] <= DATEADD(DD, DATEDIFF(DD, 0, GETDATE()), @NumberDays)
WHERE [FAKE_DATE] > DATEADD(dd, DATEDIFF(dd, 0, GETDATE()), @StartDay)
AND [FAKE_DATE] <= DATEADD(DD, DATEDIFF(DD, 0, GETDATE()), @EndDay)
)
GO




IF OBJECT_ID('[HINDCAST].[FCT_Hindcast]') IS NOT NULL
    DROP FUNCTION [HINDCAST].[FCT_Hindcast];
GO
CREATE FUNCTION [HINDCAST].[FCT_Hindcast] (
    @Latitude AS float,
    @Longitude AS float,
    @NumberDays AS int
)
RETURNS @T TABLE (
    --~ [DUNY] [int],
    --~ [LAST_DATE] [datetime],
    --~ [DSYS] [int],
    --~ [FIRST_DATE] [datetime],
    --~ [NYEO] [int],
    --~ [END_NEXT_DATE] [datetime],
    --~ [DaysLeft] [int],
    --~ [DaysPicked] [int],
    --~ [StartDay] [datetime],
    --~ [EndDay] [datetime],
    [Generated] [datetime],
    [ForTime] [datetime],
    [Model] varchar(20),
    [Member] [int],
    [Latitude] [float],
    [Longitude] [float],
    [TMP] [float],
    [RH] [float],
    [WS] [float],
    [WD] [float],
    [APCP] [float],
    [DISTANCE_FROM] [float]
)
AS
BEGIN
    DECLARE @DaysUntilNextYear AS int
    DECLARE @DaysSinceYearStart AS int
    DECLARE @NextYearEndOffset AS int
    DECLARE @CurrentOffset AS int
    DECLARE @CurrentStart AS int
    DECLARE @CurrentEnd AS int
    DECLARE @DaysPicked AS int
    -- NOTE: this is until Jan 1 @ 00:00:00 since we pick dates <= it and we need 18z of Dec 31
    SET @DaysUntilNextYear = DATEDIFF(DD,GETDATE(),DATEADD(YY,DATEDIFF(YY,-1,GETDATE()),0))
    SET @DaysSinceYearStart = DATEDIFF(DD,GETDATE(),DATEADD(YY,DATEDIFF(YY,0,GETDATE()),0))
    SET @CurrentStart = 0
    SET @CurrentOffset = 0
    IF @NumberDays <= @DaysUntilNextYear
        SET @CurrentEnd = @NumberDays
    ELSE
        SET @CurrentEnd = @DaysUntilNextYear
    SET @DaysPicked = 1
    WHILE @NumberDays > @DaysPicked BEGIN
        SET @DaysPicked = @DaysPicked + (@CurrentEnd - @CurrentStart - 1)
        INSERT @T
        SELECT
            --~ @NumberDays AS [DaysLeft],
            --~ @DaysPicked AS [DaysPicked],
            *
        FROM [HINDCAST].[FCT_Hindcast_Slice](@Latitude, @Longitude, @CurrentStart, @CurrentEnd, @CurrentOffset)
        WHERE [Member] IN (SELECT [YEAR] FROM [HINDCAST].[HINDCAST].[DAT_Model])
        SET @CurrentStart = @DaysSinceYearStart
        IF @NumberDays < @DaysPicked + 365
            SET @CurrentEnd = @CurrentStart + (@NumberDays - @DaysPicked) + 1
        ELSE
            SET @CurrentEnd = @DaysUntilNextYear
        SET @CurrentOffset = @CurrentOffset + 1
    END
    RETURN
END
GO

--SELECT *
--FROM [HINDCAST].[FCT_All_Closest](46.5, -85)
--WHERE [FAKE_DATE] > DATEADD(dd, DATEDIFF(dd, 0, GETDATE()), -210)
--AND [FAKE_DATE] <= DATEADD(DD, DATEDIFF(DD, 0, GETDATE()), -200)
--ORDER BY LocationModelId, ForTime

--SELECT * FROM [HINDCAST].[FCT_Hindcast_Slice](46.5, -85, -250, -215, 1)

--~ SELECT MAX(YEAR(ForTime)), [Member]
--~ FROM [HINDCAST].[FCT_Hindcast](46.5, -85, 900)
--~ GROUP BY [Member]

--~ SELECT *
--~ FROM [HINDCAST].[FCT_Hindcast](46.5, -85, 900)
--~ Where [Member]=1948
--~ ORDER BY [Member], [ForTime]

