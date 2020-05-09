#### 2.2. Scoring

##### 2.2.1. Base metric: Root Mean Squared Scaled Error

The sales data we are given are sampled with a daily frequency.

For a given time series $(y_t)_{1\le t\le T+H}$, $T$ is the training cutoff time, $H$ (=28 days) is the prediction horizon.

A forecast estimate of $y$, $\hat{y}$ can be evaluated with the Root Mean Square Scaled Error:

$$RMSSE = \frac{\sqrt{\frac{1}{H}\sum_{i=1}^H (y_{T+i} - \hat{y_{T+i}})^2}}{\sqrt{\frac{1}{T-1}\sum_{i=2}^T (y_{i} - y_{i-1})^2}}$$

This error can be interpreted as a root mean square error (RMSE), scaled by the RMSE of a lag-1 predictor on the training data.

##### 2.2.2. Levels of aggregation

The sales time series are provided are all provided at the lowest level aggregation, which is "Sales per day for each item  id, in each store".

Furthermore, each item comes with attributes:
- **category**
- **department**

Each store belongs to a **state** (one of CA, TX, WI).

Therefore, sales numbers can be summed at different levels of aggregation.

The challenge suggests to evaluate forecasts at different levels of aggregation, namely:
- all sales
- by `state_id`
- by `store_id`
- by `category_id`
- by `dept_id`
- by (`state_id`, `cat_id`)
- by (`state_id`, `dept_id`)
- by (`store_id`, `cat_id`)
- by (`store_id`, `dept_id`)
- by `item_id`
- by (`state_id`, `item_id`)
- by `id`
  

##### 2.2.3. RMSSE weightage

These levels of aggregation augment the number of time series that are part of the evaluation to 42,840. Each of those do not represent the same sales volume.

This why all the RMSSEs are aggregated into a single metric called Weighted Root Mean Squared Scaled Error (WRMSSE), which accounts for difference in sales volume with a weighted sum:

$$WRMSSE = \sum_{i=1}^{42,840}w_i RMSSE_i$$

Each $w_i$ depends on the respective cumulative USD sales value over the last 28 days of the training set, as a ratio over the total USD sales, and divided by the number of aggregation levels (12).

