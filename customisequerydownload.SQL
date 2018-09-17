/*==============================================================================
STEP 1
Create SampleDB databases on the local instance
==============================================================================*/
USE [master];
GO
IF EXISTS (SELECT name FROM sys.databases WHERE name = N'SampleDB')
BEGIN
    -- Close connections to the StagingDB database
    ALTER DATABASE SampleDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE SampleDB;
END;
GO
-- Create SampleDB database and log files
CREATE DATABASE SampleDB
ON PRIMARY
       (
           NAME = N'SampleDB',
           FILENAME = N'C:\Program Files\Microsoft SQL Server\MSSQL13.MSSQL2016DEV\MSSQL\DATA\SampleDB.mdf',           
           SIZE = 10MB,
           MAXSIZE = 1GB,
           FILEGROWTH = 10MB
       )
LOG ON
    (
        NAME = N'SampleDB_log',
        FILENAME = N'C:\Program Files\Microsoft SQL Server\MSSQL13.MSSQL2016DEV\MSSQL\DATA\SampleDB_log.LDF',
        SIZE = 1MB,
        MAXSIZE = 1GB,
        FILEGROWTH = 10MB
    );
GO
--Assign database ownership to login SA
EXEC SampleDB.dbo.sp_changedbowner @loginame = N'SA', @map = false;
GO
--Change the recovery model to BULK_LOGGED
ALTER DATABASE SampleDB SET RECOVERY BULK_LOGGED;
GO
 
/*======================================================================================
STEP 2
Create sample_data table on SampleDB database and insert 10000 dummy records
imitating mocked up sales transations across random dates, postcodes and SKU numbers 
======================================================================================*/
USE SampleDB;
GO
SET NOCOUNT ON;
IF OBJECT_ID('sample_data') IS NOT NULL
BEGIN
    DROP TABLE sample_data;
END;
-- Create target object 
CREATE TABLE sample_data
(
    id INT IDENTITY(1, 1) NOT NULL,
    product_sku VARCHAR(512) NOT NULL,
    quantity INT NOT NULL,
    sales_amount MONEY NOT NULL,
    postcode VARCHAR(4) NOT NULL,
    state VARCHAR(128) NOT NULL,
    order_date DATETIME NOT NULL
);
-- Populate target object with dummy data
DECLARE @postcodestate TABLE
(
    id INT IDENTITY(1, 1),
    postcode VARCHAR(4),
    state VARCHAR(128)
);
INSERT INTO @postcodestate
(
    postcode,
    state
)
SELECT '2580', 'NSW' UNION ALL SELECT '2618', 'NSW' UNION ALL SELECT '2618', 'NSW' UNION ALL SELECT '2581', 'NSW' UNION ALL
SELECT '2582', 'NSW' UNION ALL SELECT '2580', 'NSW' UNION ALL SELECT '2550', 'NSW' UNION ALL SELECT '2550', 'NSW' UNION ALL
SELECT '2450', 'NSW' UNION ALL SELECT '3350', 'VIC' UNION ALL SELECT '3350', 'VIC' UNION ALL SELECT '3212', 'VIC' UNION ALL
SELECT '3215', 'VIC' UNION ALL SELECT '3880', 'VIC' UNION ALL SELECT '3759', 'VIC' UNION ALL SELECT '3037', 'VIC' UNION ALL
SELECT '3631', 'VIC' UNION ALL SELECT '4006', 'QLD' UNION ALL SELECT '4069', 'QLD' UNION ALL SELECT '4171', 'QLD' UNION ALL
SELECT '4852', 'QLD' UNION ALL SELECT '4852', 'QLD' UNION ALL SELECT '4352', 'QLD' UNION ALL SELECT '4701', 'QLD' UNION ALL
SELECT '4218', 'QLD' UNION ALL SELECT '5095', 'SA'  UNION ALL SELECT '5097', 'SA'  UNION ALL SELECT '5573', 'SA'  UNION ALL
SELECT '5700', 'SA'  UNION ALL SELECT '5214', 'SA'  UNION ALL SELECT '6209', 'WA'  UNION ALL SELECT '6054', 'WA'  UNION ALL
SELECT '6068', 'WA'  UNION ALL SELECT '6430', 'WA'  UNION ALL SELECT '6770', 'WA'  UNION ALL SELECT '7054', 'TAS' UNION ALL
SELECT '7253', 'TAS' UNION ALL SELECT '7140', 'TAS' UNION ALL SELECT '7179', 'TAS' UNION ALL SELECT '7109', 'TAS' UNION ALL
SELECT '0870', 'NT'  UNION ALL SELECT '0872', 'NT'  UNION ALL SELECT '0852', 'NT'  UNION ALL SELECT '2617', 'ACT' UNION ALL
SELECT '2617', 'ACT' UNION ALL SELECT '2913', 'ACT' UNION ALL SELECT '2905', 'ACT' UNION ALL SELECT '2903', 'ACT';
DECLARE @allchars VARCHAR(100) = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
DECLARE @max_row_number INT;
SET @max_row_number = 10000;
DECLARE @count INT = 1;
WHILE @count &lt;= @max_row_number
BEGIN
    INSERT INTO SampleDB.dbo.sample_data
    (
        product_sku,
        quantity,
        sales_amount,
        postcode,
        state,
        order_date
    )
    SELECT RIGHT(LEFT(@allchars, ABS(BINARY_CHECKSUM(NEWID()) % 35) + 1), 1)
           + RIGHT(LEFT(@allchars, ABS(BINARY_CHECKSUM(NEWID()) % 35) + 1), 1)
           + RIGHT(LEFT(@allchars, ABS(BINARY_CHECKSUM(NEWID()) % 35) + 1), 1)
           + RIGHT(LEFT(@allchars, ABS(BINARY_CHECKSUM(NEWID()) % 35) + 1), 1)
           + RIGHT(LEFT(@allchars, ABS(BINARY_CHECKSUM(NEWID()) % 35) + 1), 1),
           CAST(RAND() * 5 + 3 AS INT),
           CAST(RAND() * 50 AS INT) / 2.5,
           (
               SELECT TOP 1 postcode FROM @postcodestate ORDER BY NEWID()
           ),
           (
               SELECT TOP 1 state FROM @postcodestate ORDER BY NEWID()
           ),
           GETDATE() - (365 * 3 * RAND() - 365);
    SET @count = @count + 1;
END;
