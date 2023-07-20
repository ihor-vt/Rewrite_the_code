import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def generate_example_data():
    """
    The generate_example_data function generates
    a DataFrame with random OHLC data.

    :return: A pandas dataframe
    """
    np.random.seed(42)
    date_rng = pd.date_range(start="2023-01-01", end="2023-07-01", freq="D")
    df = pd.DataFrame(date_rng, columns=["timestamp"])
    df["open"] = np.random.uniform(100, 150, size=(len(date_rng),))
    df["high"] = df["open"] + np.random.uniform(0, 10, size=(len(date_rng),))
    df["low"] = df["open"] - np.random.uniform(0, 10, size=(len(date_rng),))
    df["close"] = np.random.uniform(df["low"], df["high"],
                                    size=(len(date_rng),))
    return df


def data_preparation(data, range_val):
    """
    The data_preparation function is used to prepare
    the data for the Bullish and Bearish Engulfing patterns.
        It creates new columns in the dataframe that will
        be used later on to determine if a pattern has been found.

    :param data: Pass the dataframe to the function
    :param range_val: Define the range of data to be used in
    the rolling function
    :return: A dataframe with the following columns:
    """
    data["structure_low"] = data["low"].rolling(range_val).min().shift(1)
    data["structure_low_index"] = (
        data["low"].rolling(range_val).apply(lambda x: x.idxmin()).shift(1)
    )

    data["lastDown"] = np.where(
        data["close"] < data["open"], data["high"], np.nan)
    data["lastDownIndex"] = np.where(
        data["close"] < data["open"], data.index, np.nan)
    data["lastLow"] = np.where(
        data["close"] < data["open"], data["low"], np.nan)

    data["lastUp"] = np.where(
        data["close"] > data["open"], data["close"], np.nan)
    data["lastUpIndex"] = np.where(
        data["close"] > data["open"], data.index, np.nan)
    data["lastUpOpen"] = np.where(
        data["close"] > data["open"], data["open"], np.nan)
    data["lastUpLow"] = np.where(
        data["close"] > data["open"], data["low"], np.nan)
    data["lastHigh"] = data["high"]
    data["lastBullBreakLow"] = 0.0

    return data


def add_bear_order_block(
    data, i, short_boxes, show_bearish_bos, last_long_index, bearish_ob_color
):
    """
    The add_bear_order_block function is used to add
    a bearish order block to the chart.

    :param data: Access the dataframe that is being plotted
    :param i: Iterate through the dataframe
    :param short_boxes: Store the data for the boxes that
    are drawn on the chart
    :param show_bearish_bos: Determine whether or not to
    show the bearish breakout structure lines
    :param last_long_index: Find the last long candle
    :param bearish_ob_color: Set the color of the bearish order block
    :return: A list of dictionaries
    """
    low_index = data.columns.get_loc("low")
    high_index = data.columns.get_loc("high")

    left = data.index[last_long_index]
    top = data.iat[last_long_index, high_index]
    bottom = data.iat[last_long_index, low_index]

    short_boxes.append(
        {
            "left": left,
            "top": top,
            "bottom": bottom,
            "right": data.index[last_long_index],
            "bgcolor": bearish_ob_color,
        }
    )

    if show_bearish_bos:
        bos_lines.append(
            {
                "x0": data["structure_low_index"][i],
                "y0": data["structure_low"][i],
                "x1": data.index[i],
                "y1": data["structure_low"][i],
                "color": "red",
                "linewidth": 2,
            }
        )

    data.at[i, "BosCandle"] = True
    data.at[i, "CandleColourMode"] = 0


def add_bull_order_block(
    data, i, long_boxes, show_bullish_bos, last_short_index, bullish_ob_color
):
    """
    The add_bull_order_block function is used to add
    a bullish order block to the chart.

    :param data: Access the dataframe
    :param i: Get the current index of the dataframe
    :param long_boxes: Store the data for the boxes that are drawn on the chart
    :param show_bullish_bos: Determine whether to show the bullish
    breakout signal or not
    :param last_short_index: Get the index of the last short candle
    :param bullish_ob_color: Set the color of the bullish order block
    :return: The dataframe with the new order block added
    """
    low_index = data.columns.get_loc("low")
    close_index = data.columns.get_loc("close")

    left = data.index[last_short_index]
    top = data.iat[last_short_index, close_index]
    bottom = data.iat[last_short_index, low_index]

    long_boxes.append(
        {
            "left": left,
            "top": top,
            "bottom": bottom,
            "right": data.index[last_short_index],
            "bgcolor": bullish_ob_color,
        }
    )

    if show_bullish_bos:
        bos_lines.append(
            {
                "x0": left,
                "y0": top,
                "x1": data.index[i],
                "y1": top,
                "color": "green",
                "linewidth": 1,
            }
        )

    data.at[i, "BosCandle"] = True
    data.at[i, "CandleColourMode"] = 1
    data.at[i, "lastBullBreakLow"] = data.at[i, "low"]


def remove_long_boxes(data, i, long_boxes):
    """
    The remove_long_boxes function removes any long boxes
    that have been closed out.

    :param data: Access the data from the csv file
    :param i: Iterate through the data
    :param long_boxes: Store the long boxes
    :return: The list of long boxes that are still valid
    """
    for j in range(len(long_boxes) - 1, -1, -1):
        lbox = long_boxes[j]
        bottom = lbox["bottom"]
        if data["close"][i] < bottom:
            del long_boxes[j]


def order_blocks(
    data, range_val,
    show_pd=False,
    show_bearish_bos=False,
    show_bullish_bos=False
):
    """
    The order_blocks function takes in a DataFrame of OHLCV data and returns
    a new DataFrame with the following columns:

    :param data: Pass the dataframe to the function
    :param range_val: Determine the range of the bos candles
    :param show_pd: Show the pandas dataframe
    :param show_bearish_bos: Show the bearish bos candles
    :param show_bullish_bos: Show the bullish breakout signals
    :return: A tuple with 4 values
    """
    bos_lines = []
    data["CandleColourMode"] = 0
    data["BosCandle"] = False

    # Create a DataFrame to store long and short order indices
    order_indices_df = pd.DataFrame(
        index=data.index, columns=["long_order", "short_order"]
    )
    order_indices_df["long_order"] = np.nan
    order_indices_df["short_order"] = np.nan

    for i in range(2, len(data)):
        if data.loc[i, "close"] < data.loc[i - 1, "close"]:
            if data.loc[i - 1, "close"] < data.loc[i - 2, "close"]:
                if (
                    data.loc[i, "low"] < data.loc[i - 1, "low"]
                    and data.loc[i - 1, "low"] < data.loc[i - 2, "low"]
                ):
                    data.at[i, "BosCandle"] = True
                    data.at[i, "CandleColourMode"] = -1

        if data.loc[i, "close"] > data.loc[i - 1, "close"]:
            if data.loc[i - 1, "close"] > data.loc[i - 2, "close"]:
                if (
                    data.loc[i, "low"] > data.loc[i - 1, "low"]
                    and data.loc[i - 1, "low"] > data.loc[i - 2, "low"]
                ):
                    data.at[i, "BosCandle"] = True
                    data.at[i, "CandleColourMode"] = 1
                    data.at[i, "lastBullBreakLow"] = data.at[i, "low"]

        # Update order indices in the DataFrame
        if data.at[i, "CandleColourMode"] == 1:
            order_indices_df.at[i, "long_order"] = i
        elif data.at[i, "CandleColourMode"] == -1:
            order_indices_df.at[i, "short_order"] = i

    order_indices_df.dropna(how="all", inplace=True)

    data["CandleColour"] = data["CandleColourMode"].map(color_mapping)

    # Only keep rows with valid 'CandleColour' values
    data = data[data["CandleColour"].notna()]

    return (
        data,
        order_indices_df["long_order"],
        order_indices_df["short_order"],
        bos_lines,
    )


df = generate_example_data()
color_mapping = {"r": "red", "b": "blue"}

# Call the function with the necessary parameters
result_df, long_order_indices, short_order_indices, bos_lines = order_blocks(
    data=df,
    range_val=15,
    show_pd=False,
    show_bearish_bos=False,
    show_bullish_bos=False
)

# Make a copy of the DataFrame to avoid SettingWithCopyWarning
result_df_copy = result_df.copy()

# Drop rows with missing 'CandleColour' values in the copy
result_df_copy.dropna(subset=["CandleColour"], inplace=True)

# Check if there are valid 'CandleColour' values to plot
if not result_df_copy.empty:
    # Plot the resulting DataFrame
    plt.figure(figsize=(12, 6))

    # Plot candles
    plt.plot(
        result_df_copy["timestamp"],
        result_df_copy["close"],
        color=result_df_copy["CandleColour"],
    )

    # Plot additional lines for bos_lines
    for line in bos_lines:
        plt.plot(
            [line["x0"], line["x1"]],
            [line["y0"], line["y1"]],
            color=line["color"],
            linewidth=line["linewidth"],
        )

    plt.show()
else:
    print("No valid CandleColour values to plot.")
