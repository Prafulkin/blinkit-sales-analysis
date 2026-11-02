SELECT * FROM blinkit_data
SELECT COUNT(*) FROM blinkit_data
USE blinkit_db
-- Data Cleaning

UPDATE blinkit_data
SET Item_Fat_Content = 
CASE
WHEN Item_Fat_Content IN ('LF', 'low fat') THEN 'Low Fat'
WHEN Item_Fat_Content = 'reg' THEN 'Regular'
ELSE Item_Fat_Content
END

SELECT DISTINCT(Item_Fat_Content) From blinkit_data
-- KPI 


SELECT * FROM blinkit_data


SELECT CAST(SUM(Total_Sales)/ 1000000 AS DECIMAL(10,2)) AS Total_Sales
FROM blinkit_data
--WHERE Outlet_Establishment_Year = 2022

SELECT CAST(AVG(Total_Sales) AS DECIMAL(10,1)) AS Avg_Sales FROM blinkit_data
WHERE Outlet_Establishment_Year = 2022

SELECT COUNT(*) AS No_of_Items FROM blinkit_data
WHERE Outlet_Establishment_Year = 2022

SELECT CAST(AVG(Rating) AS DECIMAL(10,2)) AS Avg_Rating FROM blinkit_data 

-- Granular Requirements 
--1 Total Sales by Fat Content:
SELECT * FROM blinkit_data

SELECT 
    Item_Fat_Content, 
    CAST(SUM(Total_Sales)/1000 AS DECIMAL(10,2)) AS Total_Sales_Thousands,
    CAST(AVG(Total_Sales) AS DECIMAL(10,1)) AS Avg_Sales,
    COUNT(*) AS No_of_Items,
    CAST(AVG(Rating) AS DECIMAL(10,2)) AS Avg_Rating
FROM blinkit_data
GROUP BY Item_Fat_Content
ORDER BY Total_Sales_Thousands DESC;



-- 2 Total Sales by Item Type:
SELECT TOP 5 Item_Type,
    CAST(SUM(Total_Sales) AS DECIMAL(10,2)) AS Total_Sales,
    CAST(AVG(Total_Sales) AS DECIMAL(10,1)) AS Avg_Sales,
    COUNT(*) AS No_of_Items,
    CAST(AVG(Rating) AS DECIMAL(10,2)) AS Avg_Rating
FROM blinkit_data
GROUP BY Item_Type
ORDER BY Total_Sales ASC;


-- 3 Fat Content by Outlet for Total Sales:

SELECT Outlet_Location_Type, 
       ISNULL([Low Fat], 0) AS Low_Fat, 
       ISNULL([Regular], 0) AS Regular
FROM 
(
    SELECT Outlet_Location_Type, Item_Fat_Content, 
           CAST(SUM(Total_Sales) AS DECIMAL(10,2)) AS Total_Sales
    FROM blinkit_data
    GROUP BY Outlet_Location_Type, Item_Fat_Content
) AS SourceTable
PIVOT 
(
    SUM(Total_Sales) 
    FOR Item_Fat_Content IN ([Low Fat], [Regular])
) AS PivotTable
ORDER BY Outlet_Location_Type;


-- 4 Total Sales by Outlet Establishment:

SELECT Outlet_Establishment_Year, 
CAST(SUM(Total_Sales) AS DECIMAL(10,2)) AS Total_Sales,
CAST(AVG(Total_Sales) AS DECIMAL(10,1)) AS Avg_Sales,
COUNT(*) AS No_of_Items,
CAST(AVG(Rating) AS DECIMAL(10,2)) AS Avg_Rating
FROM blinkit_data
GROUP BY Outlet_Establishment_Year
ORDER BY Outlet_Establishment_Year


-- Percentage of Sales by Outlet Size
SELECT 
    Outlet_Size, 
    CAST(SUM(Total_Sales) AS DECIMAL(10,2)) AS Total_Sales,
    CAST((SUM(Total_Sales) * 100.0 / SUM(SUM(Total_Sales)) OVER()) AS DECIMAL(10,2)) AS Sales_Percentage
FROM blinkit_data
GROUP BY Outlet_Size
ORDER BY Total_Sales DESC;

-- Sales by Outlet Location

SELECT Outlet_Location_Type, 
CAST(SUM(Total_Sales) AS DECIMAL(10,2)) AS Total_Sales,
CAST((SUM(Total_Sales) * 100.0 / SUM(SUM(Total_Sales)) OVER()) AS DECIMAL(10,2)) AS Sales_Percentage,
CAST(AVG(Total_Sales) AS DECIMAL(10,1)) AS Avg_Sales,
COUNT(*) AS No_of_Items,
CAST(AVG(Rating) AS DECIMAL(10,2)) AS Avg_Rating

FROM blinkit_data
GROUP BY Outlet_Location_Type
ORDER BY Total_Sales DESC
-- add where condition for Outlet_Establishment_year and test.



--- High level of Insights 

-- 1 Find the outlet with the highest total sales and its average rating

SELECT 
    Outlet_Identifier,
    CAST(SUM(Total_Sales) AS DECIMAL(12,2)) AS Total_Sales,
    CAST(AVG(Rating) AS DECIMAL(4,2)) AS Avg_Rating
FROM 
    blinkit_data
GROUP BY 
    Outlet_Identifier
ORDER BY 
    Total_Sales DESC;

--2 Which product type (Item_Type) contributes the most to total sales, and how does its average visibility compare with others?

WITH ItemTypeSales AS (
    SELECT
        Item_Type,
        CAST(SUM(Total_Sales) AS DECIMAL(12,2)) AS Total_Sales,
        CAST(AVG(Item_Visibility) AS DECIMAL(10,4)) AS Avg_Visibility
    FROM blinkit_data
    GROUP BY Item_Type
)
SELECT
    Item_Type,
    Total_Sales,
    Avg_Visibility,
    RANK() OVER (ORDER BY Total_Sales DESC) AS Sales_Rank,
    CAST(AVG(Avg_Visibility) OVER () AS DECIMAL(10,4)) AS Overall_Avg_Visibility,
    CAST(Avg_Visibility - AVG(Avg_Visibility) OVER () AS DECIMAL(10,4)) AS Visibility_Difference
FROM ItemTypeSales
ORDER BY Sales_Rank;

-- 3 Which items have consistently high ratings but below-average visibility — indicating under-promoted high-quality products?
-- Which items have consistently high ratings but below-average visibility?

SELECT 
    Item_Identifier,
    Item_Type,
    Total_Sales,
    Rating,
    Item_Visibility
FROM blinkit_data
WHERE Rating > (SELECT AVG(Rating) FROM blinkit_data)
  AND Item_Visibility < (SELECT AVG(Item_Visibility) FROM blinkit_data)
ORDER BY Rating DESC, Total_Sales DESC;



-- 4 All Metrics by Outlet Type:
SELECT Outlet_Type, 
CAST(SUM(Total_Sales) AS DECIMAL(10,2)) AS Total_Sales,
		CAST(AVG(Total_Sales) AS DECIMAL(10,0)) AS Avg_Sales,
		COUNT(*) AS No_Of_Items,
		CAST(AVG(Rating) AS DECIMAL(10,2)) AS Avg_Rating,
		CAST(AVG(Item_Visibility) AS DECIMAL(10,2)) AS Item_Visibility
FROM blinkit_data
GROUP BY Outlet_Type
ORDER BY Total_Sales DESC
