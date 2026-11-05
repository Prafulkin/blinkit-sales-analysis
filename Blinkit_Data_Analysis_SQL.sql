/*
Blinkit sales analysis - SQL Server (T-SQL)
Input table: dbo.blinkit_data in blinkit_db.
Expected source-style columns: Item_Fat_Content, Item_Identifier, Item_Type,
Outlet_Establishment_Year, Outlet_Identifier, Outlet_Location_Type, Outlet_Size,
Outlet_Type, Item_Visibility, Item_Weight, Total_Sales, Rating.
Import the cleaned snapshot using the column names above (including canonical
Low Fat / Regular labels). The cleaning check below is a SELECT preview;
analysis does not mutate source data.
*/
USE blinkit_db;
GO

-- 1. Source profile and non-destructive fat-content normalization preview.
SELECT COUNT_BIG(*) AS Record_Count FROM dbo.blinkit_data;
WITH Fat_Content_Preview AS (
    SELECT CASE WHEN LOWER(LTRIM(RTRIM(Item_Fat_Content))) IN ('lf', 'low fat') THEN 'Low Fat'
             WHEN LOWER(LTRIM(RTRIM(Item_Fat_Content))) IN ('reg', 'regular') THEN 'Regular'
             ELSE LTRIM(RTRIM(Item_Fat_Content)) END AS Standardized_Fat_Content,
         COUNT_BIG(*) AS Record_Count
    FROM dbo.blinkit_data
    GROUP BY CASE WHEN LOWER(LTRIM(RTRIM(Item_Fat_Content))) IN ('lf', 'low fat') THEN 'Low Fat'
               WHEN LOWER(LTRIM(RTRIM(Item_Fat_Content))) IN ('reg', 'regular') THEN 'Regular'
               ELSE LTRIM(RTRIM(Item_Fat_Content)) END
)
SELECT Standardized_Fat_Content, Record_Count
FROM Fat_Content_Preview
ORDER BY Standardized_Fat_Content;

-- 2. Core KPIs. All use the same unfiltered row population; establishment year
-- is an outlet attribute, not a transaction-date filter.
SELECT CAST(SUM(Total_Sales) AS DECIMAL(18, 4)) AS Total_Sales,
       CAST(AVG(Total_Sales) AS DECIMAL(18, 4)) AS Average_Sales_Per_Record,
       COUNT(Total_Sales) AS Number_Of_Records,
       CAST(AVG(Rating) AS DECIMAL(10, 4)) AS Average_Rating
FROM dbo.blinkit_data;

-- 3. Sales by fat content, in source sales units (no currency inferred).
SELECT Item_Fat_Content,
       SUM(Total_Sales) AS Total_Sales,
       AVG(Total_Sales) AS Average_Sales_Per_Record,
       COUNT(Total_Sales) AS Number_Of_Records,
       AVG(Rating) AS Average_Rating,
       100.0 * SUM(Total_Sales) / NULLIF(SUM(SUM(Total_Sales)) OVER (), 0) AS Sales_Contribution_Pct
FROM dbo.blinkit_data
GROUP BY Item_Fat_Content
ORDER BY Total_Sales DESC;

-- 4. Top five item types by total sales (highest first).
SELECT TOP (5) Item_Type,
       SUM(Total_Sales) AS Total_Sales,
       AVG(Total_Sales) AS Average_Sales_Per_Record,
       COUNT(Total_Sales) AS Number_Of_Records,
       AVG(Rating) AS Average_Rating
FROM dbo.blinkit_data
GROUP BY Item_Type
ORDER BY Total_Sales DESC, Item_Type ASC;

-- 5. Sales by location tier and fat content (conditional aggregation).
SELECT Outlet_Location_Type,
       SUM(CASE WHEN Item_Fat_Content = 'Low Fat' THEN Total_Sales ELSE 0 END) AS Low_Fat_Sales,
       SUM(CASE WHEN Item_Fat_Content = 'Regular' THEN Total_Sales ELSE 0 END) AS Regular_Sales
FROM dbo.blinkit_data
GROUP BY Outlet_Location_Type
ORDER BY Outlet_Location_Type;

-- 6. Outlet establishment year: descriptive cohort comparison, not a trend in
-- time-period sales (the dataset has no transaction dates).
SELECT Outlet_Establishment_Year,
       SUM(Total_Sales) AS Total_Sales,
       AVG(Total_Sales) AS Average_Sales_Per_Record,
       COUNT(Total_Sales) AS Number_Of_Records,
       AVG(Rating) AS Average_Rating
FROM dbo.blinkit_data
GROUP BY Outlet_Establishment_Year
ORDER BY Outlet_Establishment_Year;

-- 7. Outlet size contribution and per-record average.
SELECT Outlet_Size,
       SUM(Total_Sales) AS Total_Sales,
       100.0 * SUM(Total_Sales) / NULLIF(SUM(SUM(Total_Sales)) OVER (), 0) AS Sales_Contribution_Pct,
       AVG(Total_Sales) AS Average_Sales_Per_Record,
       COUNT(Total_Sales) AS Number_Of_Records
FROM dbo.blinkit_data
GROUP BY Outlet_Size
ORDER BY Total_Sales DESC;

-- 8. Outlet location tier contribution.
SELECT Outlet_Location_Type,
       SUM(Total_Sales) AS Total_Sales,
       100.0 * SUM(Total_Sales) / NULLIF(SUM(SUM(Total_Sales)) OVER (), 0) AS Sales_Contribution_Pct,
       AVG(Total_Sales) AS Average_Sales_Per_Record,
       COUNT(Total_Sales) AS Number_Of_Records,
       AVG(Rating) AS Average_Rating
FROM dbo.blinkit_data
GROUP BY Outlet_Location_Type
ORDER BY Total_Sales DESC;

-- 9. Outlet-level summary and share of overall sales.
WITH Outlet_Summary AS (
    SELECT Outlet_Identifier, SUM(Total_Sales) AS Total_Sales,
           AVG(Rating) AS Average_Rating, COUNT(Total_Sales) AS Number_Of_Records
    FROM dbo.blinkit_data
    GROUP BY Outlet_Identifier
)
SELECT Outlet_Identifier, Total_Sales,
       100.0 * Total_Sales / NULLIF(SUM(Total_Sales) OVER (), 0) AS Sales_Contribution_Pct,
       Average_Rating, Number_Of_Records,
       RANK() OVER (ORDER BY Total_Sales DESC) AS Sales_Rank
FROM Outlet_Summary
ORDER BY Sales_Rank, Outlet_Identifier;

-- 10. Item-type sales and visibility association. Descriptive only; it does not
-- imply that visibility causes sales.
WITH Item_Type_Summary AS (
    SELECT Item_Type, SUM(Total_Sales) AS Total_Sales,
           AVG(Item_Visibility) AS Average_Item_Visibility,
           AVG(Rating) AS Average_Rating
    FROM dbo.blinkit_data
    GROUP BY Item_Type
)
SELECT Item_Type, Total_Sales, Average_Item_Visibility, Average_Rating,
       RANK() OVER (ORDER BY Total_Sales DESC) AS Sales_Rank
FROM Item_Type_Summary
ORDER BY Sales_Rank, Item_Type;

/* Additional Business Analysis
   Each query answers one requested question. All values are snapshot summaries. */

-- 1. Which outlet contributes the highest percentage of total sales?
WITH Outlet_Sales AS (
    SELECT Outlet_Identifier, SUM(Total_Sales) AS Total_Sales
    FROM dbo.blinkit_data GROUP BY Outlet_Identifier
)
SELECT TOP (1) Outlet_Identifier, Total_Sales,
       100.0 * Total_Sales / NULLIF(SUM(Total_Sales) OVER (), 0) AS Sales_Contribution_Pct
FROM Outlet_Sales ORDER BY Total_Sales DESC, Outlet_Identifier;

-- 2. Which product categories have high ratings but low sales?
-- Thresholds are dataset-wide averages; these relative cutoffs are not targets.
WITH Category_Summary AS (
    SELECT Item_Type, SUM(Total_Sales) AS Total_Sales, AVG(Rating) AS Average_Rating
    FROM dbo.blinkit_data GROUP BY Item_Type
), Thresholds AS (
    SELECT AVG(Total_Sales) AS Average_Category_Sales,
           AVG(Average_Rating) AS Average_Category_Rating FROM Category_Summary
)
SELECT c.Item_Type, c.Total_Sales, c.Average_Rating
FROM Category_Summary AS c CROSS JOIN Thresholds AS t
WHERE c.Total_Sales < t.Average_Category_Sales
  AND c.Average_Rating > t.Average_Category_Rating
ORDER BY c.Average_Rating DESC, c.Total_Sales ASC;

-- 3. Which outlets perform above the average outlet sales?
WITH Outlet_Sales AS (
    SELECT Outlet_Identifier, SUM(Total_Sales) AS Total_Sales
    FROM dbo.blinkit_data GROUP BY Outlet_Identifier
), Outlet_Average AS (
    SELECT AVG(Total_Sales) AS Average_Sales_Per_Outlet FROM Outlet_Sales
)
SELECT s.Outlet_Identifier, s.Total_Sales, a.Average_Sales_Per_Outlet
FROM Outlet_Sales AS s CROSS JOIN Outlet_Average AS a
WHERE s.Total_Sales > a.Average_Sales_Per_Outlet
ORDER BY s.Total_Sales DESC;

-- 4. What is the sales contribution of each outlet location tier?
SELECT Outlet_Location_Type, SUM(Total_Sales) AS Total_Sales,
       100.0 * SUM(Total_Sales) / NULLIF(SUM(SUM(Total_Sales)) OVER (), 0) AS Sales_Contribution_Pct
FROM dbo.blinkit_data GROUP BY Outlet_Location_Type ORDER BY Total_Sales DESC;

-- 5. What are the top three item types within each outlet type?
WITH Outlet_Type_Item_Sales AS (
    SELECT Outlet_Type, Item_Type, SUM(Total_Sales) AS Total_Sales
    FROM dbo.blinkit_data GROUP BY Outlet_Type, Item_Type
), Ranked AS (
    SELECT *, DENSE_RANK() OVER (PARTITION BY Outlet_Type ORDER BY Total_Sales DESC) AS Sales_Rank
    FROM Outlet_Type_Item_Sales
)
SELECT Outlet_Type, Item_Type, Total_Sales, Sales_Rank
FROM Ranked WHERE Sales_Rank <= 3 ORDER BY Outlet_Type, Sales_Rank, Item_Type;

-- 6. Which outlet size has the highest average sales per record?
SELECT TOP (1) Outlet_Size, AVG(Total_Sales) AS Average_Sales_Per_Record,
       SUM(Total_Sales) AS Total_Sales, COUNT(Total_Sales) AS Number_Of_Records
FROM dbo.blinkit_data GROUP BY Outlet_Size
ORDER BY Average_Sales_Per_Record DESC, Outlet_Size;

-- 7. Which item type contributes the most to total revenue (recorded sales)?
SELECT TOP (1) Item_Type, SUM(Total_Sales) AS Total_Sales,
       100.0 * SUM(Total_Sales) / NULLIF(SUM(SUM(Total_Sales)) OVER (), 0) AS Sales_Contribution_Pct
FROM dbo.blinkit_data GROUP BY Item_Type ORDER BY Total_Sales DESC, Item_Type;

-- 8. Which product categories have the lowest average ratings?
SELECT Item_Type, AVG(Rating) AS Average_Rating,
       SUM(Total_Sales) AS Total_Sales, COUNT(Rating) AS Number_Of_Ratings,
       DENSE_RANK() OVER (ORDER BY AVG(Rating) ASC) AS Rating_Rank
FROM dbo.blinkit_data GROUP BY Item_Type
ORDER BY Average_Rating ASC, Item_Type;

-- 9. How does outlet establishment year relate to sales performance?
-- Group-level total, per-record mean and count contextualize differing group sizes.
SELECT Outlet_Establishment_Year, SUM(Total_Sales) AS Total_Sales,
       AVG(Total_Sales) AS Average_Sales_Per_Record,
       COUNT(Total_Sales) AS Number_Of_Records, AVG(Rating) AS Average_Rating
FROM dbo.blinkit_data GROUP BY Outlet_Establishment_Year
ORDER BY Outlet_Establishment_Year;

-- 10. Which outlet-type and item-type combinations generate the highest sales?
SELECT TOP (20) Outlet_Type, Item_Type, SUM(Total_Sales) AS Total_Sales,
       AVG(Total_Sales) AS Average_Sales_Per_Record, COUNT(Total_Sales) AS Number_Of_Records,
       RANK() OVER (ORDER BY SUM(Total_Sales) DESC) AS Sales_Rank
FROM dbo.blinkit_data GROUP BY Outlet_Type, Item_Type
ORDER BY Total_Sales DESC, Outlet_Type, Item_Type;
