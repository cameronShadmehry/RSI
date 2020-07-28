# Necessary Libraries
import yfinance as yf, pandas as pd, shutil, os, time, glob
import numpy as np
import requests
from get_all_tickers import get_tickers as gt
from statistics import mean
# If you have a list of your own you would like to use just create a new list instead of using this, for example: tickers = ["FB", "AMZN", ...] 
tickers = ["AMZN", "CRM", "AAL", "DAL", "TSLA", "MSFT", "FB", "AAPL"]
# Check that the amount of tickers isn't more than 2000
print("The amount of stocks chosen to observe: " + str(len(tickers)))
# These two lines remove the Stocks folder and then recreate it in order to remove old stocks. Make sure you have created a Stocks Folder the first time you run this.
shutil.rmtree("<Your Path>")
os.mkdir("<Your Path>")
#  These will do the same thing but for the folder jolding the RSI values for each stock.
shutil.rmtree("<Your Path>")
os.mkdir("<Your Path>")
# Holds the amount of API calls we executed
Amount_of_API_Calls = 0
# This while loop is reponsible for storing the historical data for each ticker in our list.
# Do not make more than 2,000 calls per hour or 48,000 calls per day or Yahoo Finance may block your IP. The clause "(Amount_of_API_Calls < 1800)" below will stop the loop from making
# too many calls to the yfinance API.

# Used to make sure we don't waste too many API calls on one Stock ticker that could be having issues
Stock_Failure = 0
Stocks_Not_Imported = 0
# Used to iterate through our list of tickers
i=0
while (i < len(tickers)) and (Amount_of_API_Calls < 1800):
    try:
        print("Iteration = " + str(i))
        stock = tickers[i]  # Gets the current stock ticker
        temp = yf.Ticker(str(stock))
        Hist_data = temp.history(period="max")  # Tells yfinance what kind of data we want about this stock (In this example, all of the historical data)
        Hist_data.to_csv("<Your Path>")  # Saves the historical data in csv format for further processing later
        time.sleep(2)  # Pauses the loop for two seconds so we don't cause issues with Yahoo Finance's backend operations
        Amount_of_API_Calls += 1 
        Stock_Failure = 0
        i += 1  # Iteration to the next ticker
    except ValueError:
        print("Yahoo Finance Backend Error, Attempting to Fix")  # An error occured on Yahoo Finance's backend. We will attempt to retreive the data again
        if Stock_Failure > 5:  # Move on to the next ticker if the current ticker fails more than 5 times
            i+=1
            Stocks_Not_Imported += 1
        Amount_of_API_Calls += 1
        Stock_Failure += 1
    # Handle SSL error
    except requests.exceptions.SSLError as e:
        print("Yahoo Finance Backend Error, Attempting to Fix SSL")  # An error occured on Yahoo Finance's backend. We will attempt to retreive the data again
        if Stock_Failure > 5:  # Move on to the next ticker if the current ticker fails more than 5 times
            i+=1
            Stocks_Not_Imported += 1
        Amount_of_API_Calls += 1
        Stock_Failure += 1
print("The amount of stocks we successfully imported: " + str(i - Stocks_Not_Imported))

# Get the path for each stock file in a list
list_files = (glob.glob("<Your Path>"))
# You can use this line to limit the analysis to a portion of the stocks in the "stocks folder"
# list_files = list_files[:1]
# Create the dataframe that we will be adding the final analysis of each stock to
Compare_Stocks = pd.DataFrame(columns=["Company", "Days_Observed", "Crosses", "True_Positive", "False_Positive", "True_Negative", "False_Negative", "Sensitivity", 
"Specificity", "Accuracy", "TPR", "FPR"])
# While loop to cycle through the stock paths
for stock in list_files:
    # Dataframe to hold the historical data of the stock we are interested in.
    Hist_data = pd.read_csv(stock)
    Company = ((os.path.basename(stock)).split(".csv")[0])  # Name of the company
    # This list holds the closing prices of a stock
    prices = []
    c = 0
    # Add the closing prices to the prices list and make sure we start at greater than 2 dollars to reduce outlier calculations.
    while c < len(Hist_data):
        if Hist_data.iloc[c,4] > float(2.00):  # Check that the closing price for this day is greater than $2.00
            prices.append(Hist_data.iloc[c,4])
        c += 1
    # prices_df = pd.DataFrame(prices)  # Make a dataframe from the prices list
    i = 0
    upPrices=[]
    downPrices=[]
    #  Loop to hold up and down price movements
    while i < len(prices):
        if i == 0:
            upPrices.append(0)
            downPrices.append(0)
        else:
            if (prices[i]-prices[i-1])>0:
                upPrices.append(prices[i]-prices[i-1])
                downPrices.append(0)
            else:
                downPrices.append(prices[i]-prices[i-1])
                upPrices.append(0)
        i += 1
    x = 0
    avg_gain = []
    avg_loss = []
    #  Loop to calculate the average gain and loss
    while x < len(upPrices):
        if x <15:
            avg_gain.append(0)
            avg_loss.append(0)
        else:
            sumGain = 0
            sumLoss = 0
            y = x-14
            while y<=x:
                sumGain += upPrices[y]
                sumLoss += downPrices[y]
                y += 1
            avg_gain.append(sumGain/14)
            avg_loss.append(abs(sumLoss/14))
        x += 1
    p = 0
    RS = []
    RSI = []
    #  Loop to calculate RSI and RS
    while p < len(prices):
        if p <15:
            RS.append(0)
            RSI.append(0)
        else:
            RSvalue = (avg_gain[p]/avg_loss[p])
            RS.append(RSvalue)
            RSI.append(100 - (100/(1+RSvalue)))
        p+=1
    #  Creates the csv for each stock's RSI and price movements
    df_dict = {
        'Prices' : prices,
        'upPrices' : upPrices,
        'downPrices' : downPrices,
        'AvgGain' : avg_gain,
        'AvgLoss' : avg_loss,
        'RS' : RS,
        'RSI' : RSI
    }
    df = pd.DataFrame(df_dict, columns = ['Prices', 'upPrices', 'downPrices', 'AvgGain','AvgLoss', 'RS', "RSI"])
    df.to_csv("<Your Path>"+Company+"_RSI.csv", index = False)

    #  Code to test the accuracy of the RSI at predicting stock prices
    Days_Observed = 15
    Crosses = 0
    nothing = 0
    True_Positive = 0
    False_Positive = 0
    True_Negative = 0
    False_Negative = 0
    Sensitivity = 0
    Specificity = 0
    Accuracy = 0
    while Days_Observed < len(prices)-5:
        if RSI[Days_Observed] <= 30:
            if ((prices[Days_Observed + 1] + prices[Days_Observed + 2] + prices[Days_Observed + 3] + prices[Days_Observed + 4] + prices[Days_Observed + 5])/5) > prices[Days_Observed]:
                True_Positive += 1
            else:
                False_Negative += 1
            Crosses += 1
        elif RSI[Days_Observed] >= 70:
            if ((prices[Days_Observed + 1] + prices[Days_Observed + 2] + prices[Days_Observed + 3] + prices[Days_Observed + 4] + prices[Days_Observed + 5])/5) <= prices[Days_Observed]:
                True_Negative += 1
            else:
                False_Positive += 1
            Crosses += 1
        else:
            #Do nothing
            nothing+=1
        Days_Observed += 1
    # while Days_Observed<len(prices)-5:

    #     Days_Observed += 1
    try:
        Sensitivity = (True_Positive / (True_Positive + False_Negative)) # Calculate sensitivity
    except ZeroDivisionError:  # Catch the divide by zero error
        Sensitivity = 0
    try:
        Specificity = (True_Negative / (True_Negative + False_Positive)) # Calculate specificity
    except ZeroDivisionError:
        Specificity = 0
    try:
        Accuracy = (True_Positive + True_Negative) / (True_Negative + True_Positive + False_Positive + False_Negative) # Calculate accuracy
    except ZeroDivisionError:
        Accuracy = 0
    TPR = Sensitivity  # Calculate the true positive rate
    FPR = 1 - Specificity  # Calculate the false positive rate
    # Create a row to add to the compare_stocks
    add_row = {'Company' : Company, 'Days_Observed' : Days_Observed, 'Crosses' : Crosses, 'True_Positive' : True_Positive, 'False_Positive' : False_Positive, 
    'True_Negative' : True_Negative, 'False_Negative' : False_Negative, 'Sensitivity' : Sensitivity, 'Specificity' : Specificity, 'Accuracy' : Accuracy, 'TPR' : TPR, 'FPR' : FPR}
    Compare_Stocks = Compare_Stocks.append(add_row, ignore_index = True) # Add the analysis on the stock to the existing Compare_Stocks dataframe
Compare_Stocks.to_csv("<Your Path>", index = False)  # Save the compiled data on each stock to a csv
