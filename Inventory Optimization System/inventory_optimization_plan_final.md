# Inventory Optimization Plan — Weekly Demand Version

## 1. Purpose and Modeling Scope

This plan converts the completed demand-forecasting outputs into operational inventory policies for selected product families. The objective is to determine inventory policy parameters that minimize inventory-related cost while satisfying the target service level.

The plan uses **weekly demand only**. Daily demand and daily disaggregation are not used in this inventory optimization model.

The available demand information includes:

1. Historical actual weekly sales from the training period.
2. Historical fitted weekly sales from the forecasting models.
3. Forecasted weekly sales for the test period of approximately three weeks.

The model focuses on three product families:

| Product Family | Selected Policy Type | Reason for Policy Choice | Optimization Scope |
|---|---|---|---|
| GROCERY I | Continuous review policy: $(s,Q)$ | High-volume products that customers buy frequently. Inventory should be monitored continuously and replenished when inventory position reaches the reorder point. | Optimize safety stock $S_s$, reorder point $s$, and order quantity $Q$. |
| BEVERAGES | Continuous review policy: $(s,Q)$ | High-volume and frequently purchased products. Frequent replenishment is operationally reasonable. | Optimize safety stock $S_s$, reorder point $s$, and order quantity $Q$. |
| CLEANING | Periodic review policy: $(R,S)$ | Demand is assumed to be less frequent than Grocery I and Beverages. Weekly review is operationally simpler and less time-consuming. | Optimize safety stock $S_s$ and order-up-to level $S$. |

> **Important scope clarification:** The policy type is assumed based on operational logic. The model does not optimize whether a product family should use continuous review or periodic review. Instead, the simulation optimizes policy parameters conditional on the chosen policy type.

The model assumptions are:

| Assumption | Value Used in This Plan |
|---|---:|
| Demand time scale | Weekly |
| Lead time | $L=1$ week |
| Review period | $R=1$ week |
| Main service metric | Fill rate $\beta$ |
| Target fill rate | $\beta=0.95$ |
| Secondary service metric | Cycle service level $\alpha$ or $\text{CSL}$ |
| Lead-time uncertainty | Excluded in this version |
| Demand uncertainty | Included through forecast-error or forecast-ratio simulation |

Stochastic lead time is intentionally excluded from the first implementation because it would substantially increase simulation complexity. It can be added later after the deterministic-lead-time model is validated.

---

## 2. Weekly Notation

Because the inventory model uses weekly demand only, the index $w$ denotes week.

| Symbol | Meaning |
|---|---|
| $D_w$ | Actual weekly demand in week $w$. |
| $\hat{D}_w$ | Forecasted or fitted weekly demand in week $w$. This is the expected weekly demand path. |
| $e_w$ | Additive weekly forecast error. |
| $r_w$ | Multiplicative weekly forecast ratio. |
| $D_w^{sim,i}$ | Simulated weekly demand for week $w$ in Monte Carlo replication $i$. |
| $D_\tau^{sim,i}$ | Simulated total demand over the risk period in replication $i$. |
| $L$ | Lead time in weeks. In this plan, $L=1$. |
| $R$ | Review period in weeks. In this plan, $R=1$. |
| $\tau$ | Risk-period length in weeks. |
| $S_s$ | Safety stock. |
| $s$ | Reorder point for the continuous review $(s,Q)$ policy. |
| $Q$ | Fixed order quantity for the continuous review $(s,Q)$ policy. |
| $S$ | Order-up-to level for the periodic review $(R,S)$ policy. |

The completed forecasting system may also contain daily forecasts, but those are not used here. This plan uses the weekly forecast output directly.

---

## 3. Service-Level Logic

The primary service-level metric is **fill rate**:

$$
\beta = 1 - \frac{\text{Expected units short}}{\text{Expected demand over the relevant replenishment cycle}}
$$

Fill rate is the main metric because the selected product families have aggregate retail demand. For these families, the percentage of units satisfied is more informative than only measuring whether a stockout occurred at least once in a cycle.

The secondary service metric is cycle service level:

$$
\text{CSL} = P(D_\tau \leq \iota)
$$

where:

- $D_\tau$ is weekly demand accumulated over the risk period.
- $\iota$ is the protection level used to cover risk-period demand.
- For an $(s,Q)$ policy, $\iota=s$.
- For an $(R,S)$ policy, $\iota=S$.

Cycle service level is useful for reporting, but the optimization constraint is based on fill rate:

$$
\beta \geq 0.95
$$

---

## 4. Weekly Demand Decomposition: Expected Demand vs. Unexpected Demand

Historical weekly sales contain both predictable and unpredictable components. Predictable components include trend, seasonality, holidays, promotions, and other systematic effects. Since the forecasting model is designed to explain these patterns, safety stock should not be estimated from the full raw weekly-demand variation.

The inventory model separates weekly demand into two components:

1. **Expected weekly demand path**, represented by the weekly forecast $\hat{D}_w$.
2. **Unexpected weekly demand uncertainty**, represented by forecast errors or forecast ratios.

The expected weekly demand path is:

$$
\hat{D}_w
$$

The additive forecast error is:

$$
e_w = D_w - \hat{D}_w
$$

The multiplicative forecast ratio is:

$$
r_w = \frac{D_w}{\hat{D}_w}
$$

Because the ratio can become unstable if $\hat{D}_w$ is close to zero, the practical ratio definition should be:

$$
r_w = \frac{D_w}{\max(\hat{D}_w,\epsilon)}
$$

where $\epsilon$ is a small positive value used to avoid division by zero or near-zero forecasts.

For the multiplicative weekly uncertainty model:

$$
D_w^{sim,i} = \max(0, \hat{D}_w \cdot r_w^{sampled,i})
$$

For the additive weekly uncertainty model:

$$
D_w^{sim,i} = \max(0, \hat{D}_w + e_w^{sampled,i})
$$

where:

- $i$ is the simulation replication index.
- $D_w^{sim,i}$ is simulated weekly demand in week $w$ for replication $i$.
- $r_w^{sampled,i}$ is a sampled historical weekly forecast ratio.
- $e_w^{sampled,i}$ is a sampled historical weekly forecast error.

> **Main modeling decision:** The main inventory optimization model uses simulated weekly demand $D_w^{sim}$ and simulated weekly risk-period demand $D_\tau^{sim}$, not raw historical weekly demand $D_w$ alone and not deterministic weekly forecast $\hat{D}_w$ alone.

---

## 5. Distribution Objects Used in the Plan

To avoid mixing different sources of variation, the plan separates three distribution objects.

| Distribution Object | Symbol | Meaning | Role in the Model |
|---|---|---|---|
| Raw historical weekly demand distribution | $D_w$ | Actual observed weekly demand from historical data. | Descriptive benchmark only. It should not be the main safety-stock distribution because it contains predictable variation. |
| Weekly forecast-uncertainty distribution | $r_w$ or $e_w$ | Unexplained weekly demand variation after the forecast model has captured expected demand. | Main uncertainty input for simulation. |
| Simulated weekly demand distribution | $D_w^{sim}$ and $D_\tau^{sim}$ | Demand generated by combining the weekly forecast path with sampled uncertainty. | Main demand distribution for inventory optimization and service-level validation. |

This distinction is essential. If gamma parameters are fitted on raw weekly sales but service levels are validated using forecast-ratio simulation, then the analytical and simulation branches are not evaluating the same uncertainty source. Therefore:

- Raw weekly demand fitting is retained only for descriptive comparison.
- Weekly forecast-ratio or weekly residual fitting is used for the main simulation.
- Gamma fitting can be applied either as a benchmark to raw weekly demand or as a parametric approximation to simulated weekly risk-period demand.

---

## 6. Normality Check and Distribution Choice

A preliminary normality check showed that the selected optimization families should not be treated as normally distributed. Therefore, the inventory model will not assume normal weekly demand.

The candidate distribution approaches are:

1. Common gamma distribution.
2. Shifted gamma distribution.
3. Custom nonparametric distribution using empirical bootstrap or kernel density estimation.

The main simulation should be based on weekly forecast uncertainty. Therefore, distribution selection should be performed on one of the following:

- Weekly forecast ratios $r_w$;
- Weekly forecast residuals $e_w$; or
- Induced simulated weekly risk-period demand $D_\tau^{sim}$.

Raw weekly sales distribution fitting should be reported only as a descriptive benchmark.

---

## 7. Weekly Forecast-Uncertainty Models

### 7.1 Multiplicative Ratio Model

The multiplicative ratio model is:

$$
r_w = \frac{D_w}{\max(\hat{D}_w,\epsilon)}
$$

$$
D_w^{sim,i} = \max(0, \hat{D}_w \cdot r_w^{sampled,i})
$$

This model is useful when forecast error tends to scale with weekly demand level. For example, if high-demand weeks usually have larger absolute errors than low-demand weeks, the ratio model is often more realistic than the additive residual model.

Before using the ratio model, ratio stability must be checked:

$$
E[r_w] \approx 1
$$

If the average ratio is not close to one, then the forecast may be biased. A calibrated weekly forecast can be created as:

$$
\hat{D}_w^{calibrated} = \hat{D}_w \cdot \bar{r}
$$

Alternatively, sampled ratios can be centered:

$$
r_w^{centered} = \frac{r_w}{\bar{r}}
$$

To avoid unrealistic simulated weekly demand caused by extreme ratios, ratio values should be winsorized or capped. For example:

$$
r_w^{capped} \in [P_1(r), P_{99}(r)]
$$

or, more conservatively:

$$
r_w^{capped} \in [P_{2.5}(r), P_{97.5}(r)]
$$

### 7.2 Additive Residual Model

The additive residual model is:

$$
e_w = D_w - \hat{D}_w
$$

$$
D_w^{sim,i} = \max(0, \hat{D}_w + e_w^{sampled,i})
$$

This model is useful when forecast error is approximately stable in absolute size across weekly demand levels.

Before using the residual model, residual bias must be checked:

$$
E[e_w] \approx 0
$$

If residuals are biased, the forecast should be recalibrated before using residuals for simulation.

### 7.3 Main Choice

The ratio model will be the main uncertainty model if demand errors are proportional to the weekly forecast level. The residual model will be used as a comparison model. The final choice should be based on:

1. Bias check.
2. Tail stability.
3. Simulated weekly demand realism.
4. Service-level sensitivity.

---

## 8. Empirical Bootstrap and KDE for Custom Distribution

The custom distribution approach is the main nonparametric method. It can be implemented in two ways.

### 8.1 Empirical Bootstrap

The empirical bootstrap samples directly from historical weekly forecast ratios or residuals:

$$
r_w^{sampled} \sim \{r_1, r_2, ..., r_n\}
$$

or:

$$
e_w^{sampled} \sim \{e_1, e_2, ..., e_n\}
$$

This method is transparent and preserves the empirical shape of the observed weekly uncertainty distribution.

### 8.2 Kernel Density Estimation

Kernel Density Estimation may also be used to smooth the weekly uncertainty distribution. A Gaussian kernel can be applied with bandwidth:

$$
\text{bandwidth} = 0.9 \cdot \sigma \cdot n^{-1/5}
$$

where:

- $\sigma$ is the standard deviation of the weekly uncertainty variable being modeled.
- $n$ is the number of observations.

If KDE generates negative weekly demand values after simulation, negative probability mass should be shifted to zero:

1. Identify all grid points where $x<0$.
2. Add their probability mass to $x=0$.
3. Remove negative grid points.
4. Renormalize the PMF so the total probability equals one.

For a discretized PMF, demand moments are:

$$
\mu = \sum_i p_i x_i
$$

$$
\sigma^2 = \sum_i p_i x_i^2 - \left(\sum_i p_i x_i\right)^2
$$

$$
\sigma = \sqrt{\sigma^2}
$$

### 8.3 Recommended Main Custom Distribution

The empirical bootstrap should be treated as the simplest baseline custom distribution. KDE should be used as a smoothed alternative. The final model can compare both, but the selected distribution must produce realistic weekly risk-period demand and stable service-level results.

---

## 9. Gamma Distribution Benchmark

The gamma distribution is retained as an analytical benchmark because it supports nonnegative skewed demand and allows expected units short to be computed using the gamma loss function.

The gamma branch must be separated from the main forecast-ratio or forecast-residual simulation.

There are two possible gamma benchmark uses:

1. **Raw weekly-demand gamma benchmark:** fit gamma to historical raw weekly demand for descriptive comparison only.
2. **Weekly risk-period gamma benchmark:** fit gamma to simulated weekly risk-period demand $D_\tau^{sim}$ and use it as an analytical approximation to the main simulation.

The second use is more consistent with the main inventory model.

### 9.1 Common Gamma Distribution

For a weekly demand variable $X$ with mean $\mu$ and variance $\sigma^2$, the gamma parameters are:

$$
\theta = \frac{\sigma^2}{\mu}
$$

$$
k = \frac{\mu^2}{\sigma^2}
$$

Therefore:

$$
X \sim \Gamma(k,\theta)
$$

where:

- $k$ is the shape parameter.
- $\theta$ is the scale parameter.

### 9.2 Shifted Gamma Distribution Using Weekly $d_{min}$

Because a standard gamma distribution assigns probability density close to zero, it may be unrealistic when the observed minimum weekly demand is far above zero. To account for this, a shifted gamma benchmark can be used.

Let the weekly shift be:

$$
c = d_{min}
$$

where $d_{min}$ is the observed minimum weekly demand for a product family.

Then:

$$
X = c + Y
$$

where:

$$
Y \sim \Gamma(k_c,\theta_c)
$$

The shifted mean is:

$$
\mu_c = \mu - c
$$

The shifted variance remains:

$$
\sigma_c^2 = \sigma^2
$$

The shifted gamma parameters are:

$$
\theta_c = \frac{\sigma^2}{\mu-c}
$$

$$
k_c = \frac{(\mu-c)^2}{\sigma^2}
$$

Therefore:

$$
X \sim c + \Gamma\left(\frac{(\mu-c)^2}{\sigma^2}, \frac{\sigma^2}{\mu-c}\right)
$$

### 9.3 Caution About Weekly $d_{min}$

The value $d_{min}$ is an observed sample minimum, not a guaranteed future lower bound. Therefore, the shifted gamma using $d_{min}$ should be treated as a benchmark scenario rather than an absolute truth.

To make this robust, the shifted gamma benchmark should test multiple shift values:

$$
c \in \{0, P_1(X), d_{min}\}
$$

where:

- $c=0$ gives the common gamma benchmark.
- $c=P_1(X)$ gives a conservative lower-tail shift.
- $c=d_{min}$ gives the preferred shifted-gamma scenario.

For each shift $c$:

$$
X \sim c + \Gamma(k_c,\theta_c)
$$

$$
k_c = \frac{(\mu-c)^2}{\sigma^2}
$$

$$
\theta_c = \frac{\sigma^2}{\mu-c}
$$

This preserves the shifted-gamma idea while reducing the risk of over-constraining the lower tail.

---

## 10. Weekly Risk-Period Demand

The risk period is the interval that inventory must protect against uncertainty.

### 10.1 Continuous Review $(s,Q)$

For a continuous review $(s,Q)$ policy, the risk period is the lead time:

$$
\tau = L
$$

Since this plan assumes:

$$
L=1
$$

then:

$$
\tau = 1 \text{ week}
$$

Therefore, for GROCERY I and BEVERAGES:

$$
D_\tau^{sim,i}=D_{w+1}^{sim,i}
$$

### 10.2 Periodic Review $(R,S)$

For a periodic review $(R,S)$ policy, the risk period is the review period plus the lead time:

$$
\tau = R + L
$$

Since this plan assumes:

$$
R=1, \quad L=1
$$

then:

$$
\tau = 2 \text{ weeks}
$$

Therefore, for CLEANING:

$$
D_\tau^{sim,i}=D_{w+1}^{sim,i}+D_{w+2}^{sim,i}
$$

### 10.3 Direct Construction of Risk-Period Demand

The main simulation constructs weekly risk-period demand directly:

$$
D_\tau^{sim,i} = \sum_{j=1}^{\tau} D_{w+j}^{sim,i}
$$

This is preferred over relying only on:

$$
\sigma_\tau = \sqrt{\tau}\sigma_w
$$

because weekly demand may be autocorrelated. If weekly demand is correlated, then:

$$
Var\left(\sum_{j=1}^{\tau}D_{w+j}\right)
\neq
\sum_{j=1}^{\tau} Var(D_{w+j})
$$

More generally:

$$
Var\left(\sum_{j=1}^{\tau}D_{w+j}\right)
=
\sum_{j=1}^{\tau} Var(D_{w+j})
+
2\sum_{i<j} Cov(D_{w+i},D_{w+j})
$$

Therefore, the main model estimates weekly risk-period demand from simulated paths rather than from independence-based aggregation formulas.

The simulated risk-period mean is:

$$
E[D_\tau^{sim}] \approx \frac{1}{N}\sum_{i=1}^{N}D_\tau^{sim,i}
$$

The simulated risk-period standard deviation is:

$$
\sigma_\tau^{sim}
=
\sqrt{\frac{1}{N-1}\sum_{i=1}^{N}\left(D_\tau^{sim,i}-\bar{D}_\tau^{sim}\right)^2}
$$

---

## 11. Safety Stock and Protection Level

Safety stock is defined as the difference between the protection level and expected risk-period demand:

$$
S_s = \iota - E[D_\tau]
$$

where:

- For an $(s,Q)$ policy, $\iota=s$.
- For an $(R,S)$ policy, $\iota=S$.

### 11.1 Continuous Review $(s,Q)$ with $L=1$

For GROCERY I and BEVERAGES:

$$
\tau=L=1
$$

The reorder point is:

$$
s = E[D_L] + S_s
$$

Since $L=1$:

$$
s = E[D_{1\text{-week}}] + S_s
$$

or, using simulation:

$$
s = E[D_\tau^{sim}] + S_s
$$

where $D_\tau^{sim}$ is one-week lead-time demand.

### 11.2 Periodic Review $(R,S)$ with $R=1$ and $L=1$

For CLEANING:

$$
\tau=R+L=2
$$

The order-up-to level is:

$$
S = E[D_{R+L}] + S_s
$$

Since $R=1$ and $L=1$:

$$
S = E[D_{2\text{-week}}] + S_s
$$

or, using simulation:

$$
S = E[D_\tau^{sim}] + S_s
$$

where $D_\tau^{sim}$ is two-week risk-period demand.

### 11.3 Initial Safety Stock

The initial safety stock value can be estimated from the 95th percentile of simulated weekly risk-period demand:

$$
S_s^{initial} = Q_{0.95}(D_\tau^{sim}) - E[D_\tau^{sim}]
$$

This is only an initialization heuristic. It should not be treated as the final fill-rate solution because the 95th percentile is closer to cycle-service-level logic than fill-rate logic.

The final safety stock must be selected by checking the fill-rate constraint:

$$
\beta \geq 0.95
$$

---

## 12. Expected Units Short and Fill Rate

For a candidate protection level $\iota$, expected units short are:

$$
U_s = E[(D_\tau - \iota)^+]
$$

where:

$$
(D_\tau - \iota)^+ = \max(0,D_\tau - \iota)
$$

Using simulation:

$$
U_s^{sim} \approx \frac{1}{N}\sum_{i=1}^{N}\max(0,D_\tau^{sim,i}-\iota)
$$

The analytical fill-rate approximation is:

$$
\beta = 1 - \frac{U_s}{d_c}
$$

where $d_c$ is expected demand over the replenishment cycle.

For the analytical approximation:

$$
d_c =
\begin{cases}
Q, & \text{for } (s,Q) \\
E[D_R], & \text{for } (R,S)
\end{cases}
$$

Because $R=1$ in the periodic review policy:

$$
E[D_R]=E[D_{1\text{-week}}]
$$

For simulation validation, the preferred realized fill rate is:

$$
\beta^{sim} = 1 - \frac{\sum_w \text{Units Short}_w}{\sum_w D_w^{sim}}
$$

This simulation-based fill rate should be treated as the main validation metric because it measures the actual percentage of weekly demand satisfied across simulated paths.

Cycle service level is:

$$
\text{CSL}^{sim} = \frac{1}{N}\sum_{i=1}^{N} I(D_\tau^{sim,i} \leq \iota)
$$

where $I(\cdot)$ equals 1 if the condition is true and 0 otherwise.

---

## 13. Gamma Loss Function Benchmark

If weekly risk-period demand is approximated by a gamma distribution:

$$
D_\tau \sim \Gamma(k_\tau,\theta_\tau)
$$

then expected units short at protection level $\iota$ are:

$$
U_s = \mathcal{L}_\Gamma(\iota;k_\tau,\theta_\tau)
$$

where:

$$
\mathcal{L}_\Gamma(\iota;k_\tau,\theta_\tau)
=
\int_\iota^\infty (d-\iota) f_\Gamma(d;k_\tau,\theta_\tau)\,dd
$$

The closed-form gamma loss expression is:

$$
\mathcal{L}_\Gamma(\iota;k_\tau,\theta_\tau)
=
k_\tau\theta_\tau \left[1-F_\Gamma(\iota;k_\tau+1,\theta_\tau)\right]
-
\iota\left[1-F_\Gamma(\iota;k_\tau,\theta_\tau)\right]
$$

To target fill rate $\beta$, solve:

$$
\mathcal{L}_\Gamma(\iota;k_\tau,\theta_\tau) = d_c(1-\beta)
$$

Because there is no simple closed-form inverse of the gamma loss function, use a numerical solver:

$$
\iota^* = \arg\min_{\iota}\left|\mathcal{L}_\Gamma(\iota;k_\tau,\theta_\tau)-d_c(1-\beta)\right|
$$

Then compute:

$$
S_s = \iota^* - E[D_\tau]
$$

### 13.1 Shifted Gamma Loss Function

If:

$$
D_\tau = x_{min} + Y
$$

where:

$$
Y \sim \Gamma(k'_\tau,\theta'_\tau)
$$

then define:

$$
\iota' = \iota - x_{min}
$$

The expected units short are:

$$
U_s = \mathcal{L}_\Gamma(\iota';k'_\tau,\theta'_\tau)
$$

where:

$$
x_{min} = \tau c
$$

and $c$ may be $0$, $P_1(D_w)$, or weekly $d_{min}$ depending on the shifted-gamma scenario.

For this plan:

- For $(s,Q)$ with $L=1$, $\tau=1$, so $x_{min}=1 \cdot c$.
- For $(R,S)$ with $R=1$ and $L=1$, $\tau=2$, so $x_{min}=2 \cdot c$.

---

## 14. Cost Model

The optimization objective is to minimize total inventory-related cost while satisfying the fill-rate constraint.

The total weekly simulation cost is:

$$
\text{Total Cost}
=
H_{week}\cdot \text{Average On-Hand Inventory}
+
K\cdot \text{Number of Orders}
+
B\cdot \text{Units Short}
$$

where:

- $H_{week}$ is holding cost per unit per week.
- $K$ is fixed ordering or transaction cost per order.
- $B$ is shortage or lost-sales penalty per unit short.

### 14.1 Holding Cost

The annual holding cost rate is assumed to be:

$$
h_{annual}=15\%
$$

The weekly unit holding cost must be calculated as:

$$
H_{week}=c\cdot\frac{h_{annual}}{52}
$$

where $c$ is unit product cost.

For this project, the normalized unit cost is fixed as:

$$
c=1
$$

Therefore, the base weekly holding cost per unit is:

$$
H_{week}=1\cdot\frac{0.15}{52}=0.0028846
$$

This means the cost outputs should be interpreted as **relative cost indices**, not actual dollar costs. The model can still compare policies correctly because every candidate policy is evaluated under the same normalized cost structure. However, the final cost values should not be reported as true business dollars unless actual product unit costs are later added.

This correction is important because $15\%/52$ is a rate, not a dollar holding cost per unit. Setting $c=1$ converts the rate into a normalized per-unit weekly holding cost.

### 14.2 Ordering Cost

The base ordering cost is assumed as:

$$
K=\$25 \text{ per order}
$$

This is a reasonable base-case assumption when exact ordering, administration, and receiving costs are unavailable.

### 14.3 Shortage or Lost-Sales Cost

The base shortage-cost assumptions are:

| Product Family | Base Shortage/Lost-Sales Cost |
|---|---:|
| GROCERY I | $15 per unit short |
| BEVERAGES | $12 per unit short |
| CLEANING | $15 per unit short |

These values are assumptions because exact gross margin, customer substitution, lost goodwill, and emergency replenishment costs are unavailable. Therefore, they must be tested through sensitivity analysis.

For retail grocery-type demand, unmet demand should normally be modeled as **lost sales**, not backorders. Customers usually do not wait for grocery items to be backordered. Therefore, the main simulation will use a lost-sales assumption unless the project explicitly chooses a backorder assumption.

For lost sales:

$$
\text{Units Short}_w = \max(0,D_w^{sim}-\text{On-Hand Inventory}_w)
$$

The shortage is penalized but does not carry forward.

If a backorder extension is added later, unmet demand would carry forward as:

$$
\text{Backorder}_{w+1}
=
\text{Backorder}_w+
\text{New Shortage}_w-
\text{Backorders Fulfilled}_w
$$

---

## 15. Initial Order Quantity for $(s,Q)$ Policy

For continuous review policies, the initial order quantity can be based on EOQ:

$$
Q_0 = \sqrt{\frac{2KD_{week}}{H_{week}}}
$$

where:

- $K$ is ordering cost per order.
- $D_{week}$ is expected weekly demand.
- $H_{week}$ is unit holding cost per week.

The expected weekly demand should be based on the expected weekly forecast path or the mean simulated weekly demand:

$$
D_{week} = E[D_w^{sim}]
$$

or:

$$
D_{week} = E[\hat{D}_w]
$$

The selected interpretation must be used consistently.

---

## 16. Weekly Inventory State Variables and Event Sequence

The simulation must explicitly define inventory state transitions at the weekly level.

| Variable | Meaning |
|---|---|
| On-hand inventory | Physical inventory available to satisfy weekly demand. |
| On-order inventory | Inventory already ordered but not yet received. |
| Inventory position | On-hand inventory plus on-order inventory minus backorders, if backorders are modeled. |
| Units short | Weekly demand not satisfied from available on-hand inventory. |
| Order quantity | Quantity ordered when the ordering condition is triggered. |

For lost-sales simulation, inventory position is:

$$
\text{Inventory Position}_w = \text{On-Hand}_w + \text{On-Order}_w
$$

For backorder simulation, inventory position is:

$$
\text{Inventory Position}_w = \text{On-Hand}_w + \text{On-Order}_w - \text{Backorders}_w
$$

The weekly event sequence should be:

1. Receive orders scheduled to arrive at the beginning of week $w$.
2. Observe simulated weekly demand $D_w^{sim}$.
3. Satisfy weekly demand from on-hand inventory.
4. Record units short or lost sales.
5. Update on-hand inventory.
6. Compute inventory position.
7. Apply the inventory policy rule.
8. Place a new order if the rule requires it.
9. Schedule the order to arrive after $L=1$ week.

This sequence must be fixed before implementation because different event sequences can generate different holding cost, shortage cost, and service-level results.

---

## 17. Inventory Policy Rules

### 17.1 Continuous Review Policy: $(s,Q)$ for GROCERY I and BEVERAGES

The policy rule is:

$$
\text{If Inventory Position}_w \leq s, \text{ order } Q
$$

The reorder point is:

$$
s = E[D_L] + S_s
$$

Since $L=1$ week:

$$
s = E[D_{1\text{-week}}] + S_s
$$

The optimization variables are:

$$
S_s, Q
$$

The optimized output includes:

- Safety stock $S_s$.
- Reorder point $s$.
- Order quantity $Q$.
- Fill rate $\beta$.
- Cycle service level.
- Total cost.

### 17.2 Periodic Review Policy: $(R,S)$ for CLEANING

The policy rule is:

$$
\text{At each weekly review epoch, order enough to raise inventory position to } S
$$

The order-up-to level is:

$$
S = E[D_{R+L}] + S_s
$$

Since $R=1$ week and $L=1$ week:

$$
S = E[D_{2\text{-week}}] + S_s
$$

The review period is fixed:

$$
R=1
$$

The optimization variable is:

$$
S_s
$$

The optimized output includes:

- Safety stock $S_s$.
- Order-up-to level $S$.
- Fill rate $\beta$.
- Cycle service level.
- Total cost.

For the periodic review policy, the actual order quantity varies every week:

$$
Q_w = \max(0,S-\text{Inventory Position}_w)
$$

Therefore, $Q$ is not a fixed optimization variable for CLEANING.

---

## 18. Main Weekly Simulation Process

For each selected product family, the main simulation process is:

1. Obtain the expected weekly demand path $\hat{D}_w$ from the weekly forecasting output.
2. Calculate weekly forecast uncertainty from historical actual and fitted weekly values:

   $$
   r_w = \frac{D_w}{\max(\hat{D}_w,\epsilon)}
   $$

   or:

   $$
   e_w = D_w-\hat{D}_w
   $$

3. Check forecast bias:

   $$
   E[r_w]\approx 1
   $$

   or:

   $$
   E[e_w]\approx 0
   $$

4. Cap extreme weekly ratios or residuals if necessary.
5. Generate Monte Carlo weekly demand paths:

   $$
   D_w^{sim,i}=\max(0,\hat{D}_w\cdot r_w^{sampled,i})
   $$

   or:

   $$
   D_w^{sim,i}=\max(0,\hat{D}_w+e_w^{sampled,i})
   $$

6. Construct simulated weekly risk-period demand:

   $$
   D_\tau^{sim,i}=\sum_{j=1}^{\tau}D_{w+j}^{sim,i}
   $$

   with:

   | Policy | Product Families | $L$ | $R$ | $\tau$ |
   |---|---|---:|---:|---:|
   | $(s,Q)$ | GROCERY I, BEVERAGES | 1 | Not used | 1 week |
   | $(R,S)$ | CLEANING | 1 | 1 | 2 weeks |

7. Calculate the initial safety stock:

   $$
   S_s^{initial}=Q_{0.95}(D_\tau^{sim})-E[D_\tau^{sim}]
   $$

8. Evaluate candidate policy parameters through weekly inventory simulation.
9. Reject any candidate policy that does not satisfy:

   $$
   \beta^{sim}\geq 0.95
   $$

10. Among feasible candidates, select the one with the lowest total cost.
11. Report final policy parameters and service-level metrics.

Because the test period has only approximately three weekly observations, the test forecast should be used as the expected weekly demand path, but validation should rely on many Monte Carlo replications rather than a single three-week realization.

Recommended simulation size:

$$
N \geq 10{,}000
$$

A larger number, such as $N=100{,}000$, can be used if computation time is acceptable.

---

## 19. Optimization Methods

The plan will use two optimization approaches:

1. Two-stage grid search as the main method.
2. Threshold/local search as an exploratory comparison method.

### 19.1 Main Method: Two-Stage Grid Search

Grid search is the main method because it is transparent and easier to validate.

#### Stage 1: Coarse Grid

For $(s,Q)$ policies:

$$
Q \in \{0.25Q_0,0.50Q_0,0.75Q_0,Q_0,1.25Q_0,1.50Q_0,1.75Q_0,2.00Q_0\}
$$

$$
S_s \in \{0,0.25\sigma_\tau,0.50\sigma_\tau,0.75\sigma_\tau,...,4.00\sigma_\tau\}
$$

For $(R,S)$ policies:

$$
S_s \in \{0,0.25\sigma_\tau,0.50\sigma_\tau,0.75\sigma_\tau,...,4.00\sigma_\tau\}
$$

where $\sigma_\tau$ is the standard deviation of simulated weekly risk-period demand.

For each candidate:

1. Run the weekly inventory simulation.
2. Calculate total cost.
3. Calculate fill rate.
4. Reject the candidate if:

   $$
   \beta^{sim}<0.95
   $$

5. Keep the feasible candidate with the lowest total cost.

#### Stage 2: Fine Grid Around the Best Candidate

If the best coarse-grid candidate is $(S_s^*,Q^*)$, run a finer grid around that region.

For $(s,Q)$:

$$
Q \in [Q^*-0.25Q_0, Q^*+0.25Q_0]
$$

$$
S_s \in [S_s^*-0.25\sigma_\tau, S_s^*+0.25\sigma_\tau]
$$

For $(R,S)$:

$$
S_s \in [S_s^*-0.25\sigma_\tau, S_s^*+0.25\sigma_\tau]
$$

The final grid-search solution is the feasible candidate with the lowest total cost after the fine search.

### 19.2 Exploratory Method: Threshold/Local Search

The threshold method is retained as an experimental comparison method, but it should be reframed as a local search rather than a stopping rule based on a single poor candidate.

The local-search logic is:

1. Start from the initial candidate:

   $$
   S_s^{initial}=Q_{0.95}(D_\tau^{sim})-E[D_\tau^{sim}]
   $$

   and, for $(s,Q)$:

   $$
   Q_0=\sqrt{\frac{2KD_{week}}{H_{week}}}
   $$

2. Define step sizes:

   $$
   \Delta S_s = 0.25\sigma_\tau
   $$

   $$
   \Delta Q = 0.25Q_0
   $$

3. Evaluate neighboring candidates.

For $(s,Q)$:

$$
(S_s+\Delta S_s,Q),\quad (S_s-\Delta S_s,Q),\quad (S_s,Q+\Delta Q),\quad (S_s,Q-\Delta Q)
$$

For $(R,S)$:

$$
S_s+\Delta S_s,\quad S_s-\Delta S_s
$$

4. Reject infeasible candidates:

$$
\beta^{sim}<0.95
$$

5. Move to the feasible neighbor with the lowest cost.
6. Stop when no feasible neighbor improves cost after a defined number of rounds.

Recommended stopping rule:

$$
\text{Stop if no improvement occurs for } m \text{ consecutive rounds}
$$

where $m$ can be set to 50 or 100. The previous threshold idea can be used as a diagnostic flag, not as an automatic stopping condition:

$$
\frac{Cost_{candidate}}{Cost_{best}}>1.3
$$

This means the candidate is poor, but it does not prove the entire search should stop.

### 19.3 Final Optimizer Selection

The grid search remains the main optimization method. The threshold/local-search method is only an exploratory comparison.

If the local-search method produces a lower cost than grid search, it must be verified by:

1. Checking that $\beta^{sim}\geq 0.95$.
2. Re-running the simulation with different random seeds.
3. Confirming that the result is stable.
4. Confirming that the policy is operationally reasonable.
5. Checking whether grid search missed the region and whether the fine grid should be expanded.

---

## 20. Analytical Gamma Benchmark Validation

For each family, the analytical gamma benchmark should be compared against simulation results.

The process is:

1. Estimate or fit gamma parameters for weekly risk-period demand $D_\tau$.
2. Solve the gamma loss equation:

   $$
   \mathcal{L}_\Gamma(\iota;k_\tau,\theta_\tau)=d_c(1-\beta)
   $$

3. Compute:

   $$
   S_s=\iota^*-E[D_\tau]
   $$

4. Validate using simulated weekly risk-period demand:

   $$
   U_s^{valid}=\frac{1}{N}\sum_{i=1}^{N}\max(0,D_\tau^{sim,i}-\iota^*)
   $$

5. Calculate validation fill rate:

   $$
   \beta^{valid}=1-\frac{U_s^{valid}}{d_c}
   $$

6. Compare analytical and simulated fill rates.

If the analytical gamma benchmark and simulation differ materially, the simulation result should dominate because it uses the weekly forecast path and uncertainty structure directly.

### 20.1 Explanation: What the Analytical Gamma Benchmark Means and Why It Is Needed

The **analytical gamma benchmark** is a simplified mathematical version of the inventory problem. Instead of relying entirely on Monte Carlo simulation, it assumes that weekly risk-period demand can be represented by a gamma distribution. Under that assumption, expected units short can be calculated using the gamma loss function. This gives a direct way to estimate the protection level $\iota$, safety stock $S_s$, reorder point $s$, or order-up-to level $S$ needed to reach the target fill rate.

In this plan, the gamma benchmark is **not the main model**. The main model is the weekly forecast-ratio or forecast-residual simulation. The benchmark is used as a reference point. It helps answer the question: "If demand followed a clean gamma distribution, what inventory level would the theory recommend?"

This is useful for four reasons. First, it gives a transparent mathematical comparison against the simulation model. If the gamma solution and simulation solution are close, then the simulation result is easier to trust because an independent analytical method gives a similar answer. Second, it helps diagnose whether the simulation is behaving reasonably. If the simulation recommends an extremely different safety stock from the gamma benchmark, then the difference should be investigated. The cause may be skewness, extreme forecast-ratio tails, autocorrelation, KDE smoothing, or the shifted-gamma assumption. Third, it gives a report-friendly explanation because the gamma loss function clearly links fill rate, expected units short, and protection level. Fourth, it preserves a classical inventory-management benchmark while allowing the final decision to rely on the more realistic simulation branch.

The correct interpretation is:

> The analytical gamma benchmark is a mathematical reference model used to compare, explain, and validate the simulation-based inventory policy. It is not the final optimization engine unless its assumptions fit the simulated weekly risk-period demand well.

For this project, the final decision should still come from the simulation branch because the simulation uses the actual weekly forecast path, sampled forecast uncertainty, the chosen policy rule, and the weekly inventory event sequence.

---

## 21. Distribution-Fit Evaluation

Distribution selection should not be decided by a simple vote such as “more than three tests agree.” Instead, distribution choice should prioritize inventory-relevant fit, especially the upper tail, because safety stock and shortage risk are tail-sensitive.

The following diagnostics should be used:

| Diagnostic | Purpose | Main Use |
|---|---|---|
| RMSE between empirical and fitted CDF/PDF | Measures overall numerical fit. | General fit comparison. |
| QQ plot | Shows whether fitted distribution matches empirical quantiles. | Visual distribution validation. |
| Tail error at 90th–99th percentiles | Measures upper-tail accuracy. | Most important for safety stock. |
| KS test | Tests maximum CDF distance. | General distribution difference. |
| Anderson-Darling test | Gives more weight to tails than KS. | Tail-sensitive validation. |
| Empirical CDF comparison | Shows full distribution alignment. | Transparent visual evidence. |
| AIC/BIC | Compares parametric distributions. | Only applicable to parametric candidates. |

Final distribution choice should follow this priority:

1. Does the distribution generate realistic simulated weekly demand?
2. Does it represent the 90th–99th percentile region well?
3. Does it produce stable fill-rate estimates?
4. Does it avoid unrealistic negative or extreme weekly demand?
5. Is it simple enough to explain?

If no parametric distribution is reliable, use the empirical bootstrap or KDE custom distribution.

### 21.1 Explanation: What This Evaluation Is Used For

Distribution-fit evaluation is used to decide **how demand uncertainty should be represented before inventory optimization is performed**. It is not only a statistical exercise. It directly affects safety stock, reorder points, order-up-to levels, fill rate, shortage cost, and total cost.

In this project, the distribution being evaluated should usually be the weekly forecast-uncertainty distribution, such as $r_w$ or $e_w$, or the induced weekly risk-period demand distribution $D_\tau^{sim}$. The purpose is to determine whether a simple parametric distribution, such as common gamma or shifted gamma, is realistic enough, or whether a custom empirical method, such as bootstrap or KDE, should be used instead.

The most important part of this evaluation is the **upper tail**. Inventory policies are especially sensitive to high-demand outcomes because shortage occurs when demand exceeds the protection level. A distribution can fit the average demand well but still produce poor inventory decisions if it underestimates the 90th to 99th percentile region. For example, if the fitted distribution underestimates the upper tail, the model will recommend too little safety stock and the realized fill rate may fall below 0.95. If the fitted distribution overestimates the upper tail, the model may recommend excessive safety stock and create unnecessary holding cost.

Therefore, this evaluation is used to answer these practical questions:

1. Is gamma accurate enough to be used as an analytical benchmark?
2. Is shifted gamma more realistic than common gamma when weekly demand has a high lower bound?
3. Are empirical bootstrap or KDE safer choices because the demand uncertainty is irregular, skewed, or heavy-tailed?
4. Does the selected uncertainty model generate realistic simulated weekly demand?
5. Does the selected uncertainty model produce stable fill-rate and cost estimates?

The final distribution choice should be based on inventory consequences, not only on statistical test results. A distribution that gives a slightly worse overall RMSE but better upper-tail fit may be more appropriate for safety-stock optimization than a distribution that fits the center well but misses shortage-risk behavior.

The correct interpretation is:

> Distribution-fit evaluation is used to choose the uncertainty model that produces realistic weekly risk-period demand and reliable inventory-policy decisions. Its main purpose is to protect the fill-rate calculation and safety-stock estimate from being distorted by a poor representation of demand uncertainty.

---

## 22. Validation Strategy

The test period has only approximately three weekly observations, so it is too short to validate inventory policy performance directly. The model should therefore use two validation approaches.

### 22.1 Monte Carlo Validation on the Weekly Test Forecast Path

Use the weekly test forecast as the expected demand path and generate many simulated weekly demand paths using the forecast-uncertainty distribution.

For each candidate policy, compute:

- Average total cost.
- Fill rate.
- Cycle service level.
- Average on-hand inventory.
- Number of orders.
- Units short.
- Frequency of stockout events.

### 22.2 Historical Rolling Backtest

Use historical weekly fitted forecasts and actual weekly sales to create rolling inventory simulations over the training or validation period.

For each rolling window:

1. Use fitted weekly forecast as expected demand.
2. Use historical actual weekly sales as realized demand or use simulated weekly demand based on forecast errors.
3. Apply the inventory policy.
4. Record cost and service metrics.

This gives a stronger test of whether the policy would have worked historically.

### 22.3 Explanation: Why Validation Is Needed

Validation is needed because optimization alone only tells which candidate policy performs best **inside the assumptions of the model**. It does not automatically prove that the policy is robust, realistic, or reliable when demand varies across time.

In this project, validation is especially important because the available test forecast covers only approximately three weeks. Three weekly observations are not enough to prove that a policy can truly achieve a 0.95 fill rate. A policy could look good or bad in three weeks simply because those weeks happened to have unusually low or unusually high demand. Therefore, the test forecast should be treated as the expected weekly demand path, while Monte Carlo simulation creates many possible demand realizations around that path.

Monte Carlo validation checks whether the optimized policy still performs well under many possible weekly demand outcomes. It answers: "If the future behaves like the forecast plus realistic forecast uncertainty, how often will this policy satisfy demand, how much shortage will occur, and how much cost will it create?"

Historical rolling backtesting checks a different question: "If this policy logic had been used in the past, would it have performed reasonably across many historical windows?" This is important because historical data contain real seasonality, promotions, shocks, and changing demand levels. A rolling backtest can reveal whether the policy only works for the short test horizon or whether it remains reasonable over broader demand conditions.

Validation is also needed to detect implementation errors. For example, the calculated safety stock may appear correct, but the simulated fill rate can still fail if the inventory event sequence, lead-time handling, order-arrival timing, or lost-sales logic is wrong.

The correct interpretation is:

> Validation is the evidence step after optimization. Optimization finds the best policy under the model. Validation checks whether that policy actually delivers the target fill rate, reasonable inventory levels, and stable cost performance under repeated simulated and historical demand conditions.

For the final report, validation supports the credibility of the selected policy. Without validation, the result would only be a mathematical recommendation; with validation, it becomes an evidence-based inventory policy.


### 22.4 What to Do If Validation Fails

If validation shows that the optimized policy does **not** deliver the target fill rate, reasonable inventory levels, or stable cost performance, the policy should not be accepted as the final recommendation immediately. A failed validation result is useful diagnostic evidence showing that at least one modeling assumption, policy parameter, uncertainty model, search range, or operational rule needs to be revised.

The first step is to identify **which validation criterion failed**.

| Failed Validation Result | Likely Meaning | Corrective Action |
|---|---|---|
| Fill rate is below $0.95$ | The protection level may be too low, the uncertainty model may underestimate the upper tail, or the inventory event sequence may be creating shortages. | Increase the safety-stock search range, recheck the upper tail of $D_\tau^{sim}$, and verify lead-time/order-arrival logic. |
| Fill rate is acceptable but average inventory is too high | The policy satisfies service but may be too conservative or too costly. | Search lower safety-stock levels, recheck shortage-cost assumptions, and compare service targets such as $\beta=0.90$, $0.95$, and $0.98$. |
| Total cost is unstable across replications | The uncertainty model may contain extreme ratios/residuals, or the number of Monte Carlo replications may be too small. | Increase simulation replications, cap extreme ratios/residuals, and compare ratio bootstrap, residual bootstrap, and KDE. |
| Historical rolling backtest performs poorly but test-path simulation performs well | The short test forecast path may not represent broader historical demand conditions. | Give more weight to rolling backtest evidence and recalibrate the uncertainty model using broader historical windows. |
| Simulation differs strongly from the analytical gamma benchmark | Gamma may not represent the risk-period demand well, or the simulation may contain autocorrelation, skewness, or tail behavior that gamma cannot capture. | Treat gamma as diagnostic only and rely on simulation after confirming the simulation logic is correct. |

The correction process should follow this order.

1. **Check implementation logic first.** Confirm that inventory arrivals, demand fulfillment, lost-sales calculation, inventory position, order timing, lead time $L=1$, and review period $R=1$ are implemented exactly as defined in the plan. This should be checked before changing the model because an implementation error can make a good policy appear bad.

2. **Recheck the uncertainty model.** If fill rate is too low, the sampled ratios or residuals may not represent high-demand risk correctly. Inspect the 90th--99th percentiles of $r_w$, $e_w$, and $D_\tau^{sim}$. If the ratio model is unstable, compare it with the residual model. If KDE smooths the upper tail too much, compare it with empirical bootstrap.

3. **Expand the optimization search space.** If no feasible candidate reaches $\beta \geq 0.95$, the grid may not include enough safety stock. Expand the safety-stock range beyond $4\sigma_\tau$, for example to $5\sigma_\tau$ or $6\sigma_\tau$, and repeat the grid search. For $(s,Q)$ policies, also expand the $Q$ range if the order quantity is causing unrealistic replenishment behavior or excessive order cost.

4. **Re-optimize under the same policy type.** After correcting the uncertainty model or search range, rerun the optimization for the same assumed policy. This keeps the experiment controlled: first determine whether the original policy type can work after reasonable tuning.

5. **If the same policy type still fails, compare an alternative policy type.** For example, if CLEANING under $(R,S)$ cannot achieve stable service without excessive inventory, test $(s,Q)$ for CLEANING as an alternative-policy scenario. If GROCERY I or BEVERAGES under $(s,Q)$ creates excessive ordering or unstable cost, test $(R,S)$ as a comparison scenario.

6. **Document the failure and revision in the report.** The report should state the original assumption, the validation failure, the corrective action, and the final decision. This makes the modeling process credible because it shows that assumptions were tested rather than blindly accepted.

The decision rule should be:

> If validation fails because of implementation errors, unstable uncertainty modeling, or too narrow a search range, fix those issues and rerun the same policy. If validation fails because the assumed policy type is structurally unsuitable for the family, then change the policy assumption and conduct the modeling again for that family.

Therefore, the correct action is not automatically to discard the model. The correct action is to diagnose the reason for failure, revise the relevant component, rerun the optimization, and only then decide whether the policy assumption itself should be changed.

---

## 23. Policy-Choice Justification Statistics

The operational policy choices should be supported by simple weekly descriptive statistics.

For each selected family, calculate:

$$
CV = \frac{\sigma_w}{\mu_w}
$$

$$
\text{Demand Frequency} = \frac{\#(D_w>0)}{n}
$$

$$
\text{Zero-Demand Frequency} = \frac{\#(D_w=0)}{n}
$$

Recommended reporting table:

| Product Family | Mean Weekly Demand | Weekly Standard Deviation | Weekly CV | Weekly Demand Frequency | Weekly Zero-Demand Frequency | Chosen Policy |
|---|---:|---:|---:|---:|---:|---|
| GROCERY I | To be calculated | To be calculated | To be calculated | To be calculated | To be calculated | $(s,Q)$ |
| BEVERAGES | To be calculated | To be calculated | To be calculated | To be calculated | To be calculated | $(s,Q)$ |
| CLEANING | To be calculated | To be calculated | To be calculated | To be calculated | To be calculated | $(R,S)$ |

This table does not need to prove that the policy type is globally optimal. Its purpose is to make the operational assumption defensible.

### 23.1 Explanation: How These Statistics Make the Policy Assumption Defensible

The policy-choice statistics make the operational assumption defensible because they connect the selected policy type to measurable demand behavior instead of relying only on intuition. The model assumes $(s,Q)$ for GROCERY I and BEVERAGES and $(R,S)$ for CLEANING. These choices may be reasonable, but the report should show evidence that the assumptions are aligned with the demand pattern of each family.

For example, high mean weekly demand and high demand frequency support continuous review because frequent demand creates frequent inventory depletion risk. If a family sells every week and has large weekly volume, waiting until a periodic review date may expose the store to avoidable stockout risk. In that case, an $(s,Q)$ policy is operationally logical because inventory is replenished when inventory position reaches the reorder point.

The coefficient of variation,

$$
CV=\frac{\sigma_w}{\mu_w}
$$

shows relative demand variability. A high-volume family can have a large standard deviation simply because its sales volume is large. CV standardizes variability by the mean, so it helps compare volatility across families. A family with high demand frequency but moderate CV may be suitable for continuous replenishment because demand is steady enough to support a reorder-point rule.

Zero-demand frequency is also important. If weekly zero-demand frequency is close to zero, demand occurs almost every week. That supports policies designed for regular replenishment. If a family has more intermittent demand, periodic review may be more operationally acceptable because constant monitoring may provide less benefit.

For CLEANING, the argument for $(R,S)$ becomes more defensible if the data show lower demand frequency, lower urgency, lower volume, or more operational tolerance for weekly review compared with GROCERY I and BEVERAGES. The table does not prove that $(R,S)$ is mathematically optimal, but it shows that the assumption is not arbitrary.

The correct interpretation is:

> Policy-choice statistics provide empirical support for the assumed policy type. They do not optimize the policy class, but they justify why a continuous review policy is reasonable for high-volume, frequently demanded families and why a weekly periodic review policy may be acceptable for a less frequently replenished family.

In the final report, this section should be presented as **policy assumption justification**, not as proof of global policy optimality.


### 23.2 What to Do If the Assumed Policy Type Is Not Suitable

If evidence shows that the assumed policy type is not suitable for a product family, then yes, the assumption should be changed and the modeling should be conducted again for that family. However, the change should be based on evidence, not only on intuition.

The policy type in this plan is an **assumption**, not an optimized decision. Therefore, the first version of the model answers a conditional question:

> Given the assumed policy type, what are the best policy parameters that minimize cost while satisfying $\beta \geq 0.95$?

If the assumed policy type performs poorly, the next step is to run an **alternative-policy comparison**. This means testing the other policy type under the same weekly demand data, same forecast-uncertainty model, same cost assumptions, same lead time, and same service target.

| Product Family | Original Assumption | Alternative Test If Original Assumption Fails |
|---|---|---|
| GROCERY I | $(s,Q)$ | Test $(R,S)$ with $R=1$ and compare total cost, fill rate, inventory level, and order frequency. |
| BEVERAGES | $(s,Q)$ | Test $(R,S)$ with $R=1$ and compare total cost, fill rate, inventory level, and order frequency. |
| CLEANING | $(R,S)$ | Test $(s,Q)$ and compare whether continuous review gives better service or lower cost. |

A policy should be considered unsuitable if one or more of the following occurs:

1. It cannot achieve $\beta \geq 0.95$ after reasonable safety-stock and parameter tuning.
2. It achieves $\beta \geq 0.95$ only by holding operationally excessive inventory.
3. It produces unstable cost or service results across Monte Carlo replications or rolling backtests.
4. It creates an unrealistic ordering pattern, such as too many orders, too large orders, or frequent stockouts.
5. An alternative policy produces clearly better cost-service performance under the same assumptions.

If the original policy is unsuitable, the revised modeling process should be:

1. Keep the same weekly demand scale.
2. Keep $L=1$ unless the validation specifically shows that the lead-time assumption should be studied as a sensitivity case.
3. Keep the same uncertainty model unless validation shows that the uncertainty model itself is the cause of poor performance.
4. Replace the policy type for the affected family.
5. Redefine the risk period because the policy change changes the protection interval:
   - For $(s,Q)$: $\tau=L=1$ week.
   - For $(R,S)$: $\tau=R+L=2$ weeks.
6. Redefine the optimization variables:
   - For $(s,Q)$: optimize $S_s$ and $Q$.
   - For $(R,S)$: optimize $S_s$ and compute variable weekly order quantity $Q_w$.
7. Rerun grid search, validation, and sensitivity analysis for the new policy type.
8. Compare the original and alternative policy results in the final report.

The final report should present this as a controlled modeling revision, not as a mistake. A suitable report statement is:

> The initial policy type was selected based on operational logic. After validation, an alternative policy was tested for any family whose assumed policy did not meet the service-cost requirements. The final policy recommendation was selected based on validated cost, fill rate, inventory level, and operational feasibility.

The correct interpretation is:

> The assumed policy type is allowed to change if evidence shows that it is unsuitable. In that case, the model should be rerun for the affected product family because changing the policy type changes the risk period, decision variables, ordering rule, cost behavior, and service-level performance.

Therefore, if $(R,S)$ or $(s,Q)$ is not suitable for a family, do not force the original assumption. Change the assumption for that family, rerun the modeling, and report both the original assumption and the evidence that justified the change.

---

## 24. Sensitivity Analysis

Because holding cost, ordering cost, and shortage/lost-sales cost are assumed, sensitivity analysis is required.

| Parameter | Low | Base | High | Step |
|---|---:|---:|---:|---:|
| Annual holding cost rate $h_{annual}$ | 10% | 15% | 25% | 5% |
| Order cost $K$ | $10 | $25 | $50 | $15 |
| Shortage/lost-sales cost $B$ | 50% of base | Base | 150% of base | 25% of base |

Additional sensitivity tests should include:

| Factor | Base | Sensitivity Values | Reason |
|---|---:|---:|---|
| Fill-rate target $\beta$ | 0.95 | 0.90, 0.95, 0.98 | Tests service-level aggressiveness. |
| Lead time $L$ | 1 week | 1, 2 weeks | Tests replenishment delay risk. |
| Review period $R$ | 1 week | 1, 2 weeks | Optional sensitivity only; the base model fixes $R=1$. |
| Gamma shift $c$ | $d_{min}$ | $0$, $P_1(D_w)$, $d_{min}$ | Tests robustness of shifted-gamma assumption. |
| Ratio cap | $P_1$–$P_{99}$ | $P_{2.5}$–$P_{97.5}$, no cap | Tests effect of extreme forecast ratios. |
| Uncertainty model | Ratio bootstrap | Residual bootstrap, KDE | Tests distribution-model dependence. |

The final report should identify whether the selected policy remains stable under reasonable cost and uncertainty assumptions.

### 24.1 Explanation: Why Sensitivity Analysis Is Operationally Needed

Sensitivity analysis is operationally needed because several important cost and uncertainty inputs are assumed rather than observed from real company accounting data. In this project, annual holding cost rate, ordering cost, shortage or lost-sales cost, gamma shift, ratio cap, and uncertainty model choice all affect the recommended inventory policy. If these assumptions change, the optimal safety stock, reorder point, order quantity, order-up-to level, fill rate, and total cost may also change.

From an operational perspective, sensitivity analysis answers: "Would I make the same inventory decision if my cost assumptions are slightly wrong?" This is critical because assumed parameters are rarely exact. For example, if shortage cost is increased, the model will usually prefer more safety stock because avoiding lost sales becomes more valuable. If holding cost is increased, the model will usually prefer less inventory because carrying extra stock becomes more expensive. If order cost is increased, the model may prefer larger but less frequent orders under an $(s,Q)$ policy.

Sensitivity analysis also helps identify which parameters are most influential. If the recommended policy changes dramatically when shortage cost changes slightly, then the decision is highly sensitive to shortage-cost assumptions and should be interpreted carefully. If the policy remains stable across low, base, and high scenarios, then the recommendation is more robust.

The uncertainty-model sensitivity is equally important. If ratio bootstrap, residual bootstrap, KDE, and gamma benchmark produce very different safety stocks, then the final report should explain why one uncertainty model is more credible. If all methods produce similar policy parameters, then the policy recommendation becomes stronger.

Operationally, sensitivity analysis supports managerial decision-making in four ways:

1. It shows whether the selected policy is robust under plausible cost conditions.
2. It reveals which assumptions most strongly affect inventory decisions.
3. It prevents overconfidence in a single base-case result.
4. It gives managers a range of expected outcomes instead of only one point estimate.

The correct interpretation is:

> Sensitivity analysis is required because inventory policies are cost-sensitive and uncertainty-sensitive. It tests whether the selected policy remains reasonable when assumed inputs change. A policy that performs well across sensitivity scenarios is more operationally reliable than a policy that is optimal only under one narrow set of assumptions.

In the final report, the sensitivity section should not be treated as optional. It is the main evidence that your recommendation is robust despite using normalized unit cost $c=1$ and assumed cost parameters.

---

## 25. Final Outputs

For each product family, the final output should include:

| Product Family | Policy | Weekly Lead Time $L$ | Weekly Review Period $R$ | Risk Period $\tau$ | Safety Stock $S_s$ | Reorder Point $s$ | Order Quantity $Q$ | Order-Up-To Level $S$ | Fill Rate $\beta$ | Cycle Service Level | Total Cost |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GROCERY I | $(s,Q)$ | 1 | Not used | 1 | To be optimized | To be calculated | To be optimized | Not applicable | To be calculated | To be calculated | To be calculated |
| BEVERAGES | $(s,Q)$ | 1 | Not used | 1 | To be optimized | To be calculated | To be optimized | Not applicable | To be calculated | To be calculated | To be calculated |
| CLEANING | $(R,S)$ | 1 | 1 | 2 | To be optimized | Not applicable | Variable weekly order quantity | To be calculated | To be calculated | To be calculated | To be calculated |

For $(R,S)$, the actual weekly order quantity varies by review epoch:

$$
Q_w = \max(0,S-\text{Inventory Position}_w)
$$

Therefore, $Q$ is not a fixed optimization variable for the periodic review policy.

---

## 26. Final Modeling Architecture

The final inventory optimization architecture has two branches.

### Branch A: Analytical Gamma Benchmark

Approximate weekly risk-period demand as:

$$
D_\tau \sim \Gamma(k_\tau,\theta_\tau)
$$

or shifted gamma:

$$
D_\tau = x_{min} + \Gamma(k'_\tau,\theta'_\tau)
$$

Then solve:

$$
\mathcal{L}_\Gamma(\iota;k_\tau,\theta_\tau)=d_c(1-\beta)
$$

Then calculate:

$$
S_s=\iota^*-E[D_\tau]
$$

This branch is used as a benchmark, not the main optimization engine.

### Branch B: Main Weekly Forecast-Ratio or Forecast-Residual Simulation

Use weekly forecast uncertainty:

$$
r_w=\frac{D_w}{\max(\hat{D}_w,\epsilon)}
$$

or:

$$
e_w=D_w-\hat{D}_w
$$

Generate simulated weekly demand:

$$
D_w^{sim,i}=\max(0,\hat{D}_w\cdot r_w^{sampled,i})
$$

or:

$$
D_w^{sim,i}=\max(0,\hat{D}_w+e_w^{sampled,i})
$$

Construct weekly risk-period demand:

$$
D_\tau^{sim,i}=\sum_{j=1}^{\tau}D_{w+j}^{sim,i}
$$

with:

$$
\tau=1 \text{ for } (s,Q), \quad \tau=2 \text{ for } (R,S)
$$

Optimize:

- $S_s$ and $Q$ for $(s,Q)$.
- $S_s$ for $(R,S)$.

Subject to:

$$
\beta^{sim}\geq 0.95
$$

Objective:

$$
\min \text{Total Cost}
$$

This branch is the main inventory optimization model.

---

## 27. Implementation Readiness Checklist

Before writing code, the following decisions must be finalized:

| Decision | Status | Required Action |
|---|---|---|
| Demand time scale | Fixed | Use weekly demand only. Do not use daily demand or daily disaggregation. |
| Product families | Fixed | Use GROCERY I, BEVERAGES, and CLEANING. |
| Policy type | Fixed by assumption | Use $(s,Q)$ for GROCERY I and BEVERAGES; use $(R,S)$ for CLEANING. |
| Lead time | Fixed | Use $L=1$ week for all product families. |
| Review period | Fixed | Use $R=1$ week for CLEANING. |
| Risk period for $(s,Q)$ | Fixed | Use $\tau=L=1$ week. |
| Risk period for $(R,S)$ | Fixed | Use $\tau=R+L=2$ weeks. |
| Main service metric | Fixed | Use fill rate $\beta=0.95$. |
| Secondary service metric | Fixed | Report cycle service level. |
| Demand uncertainty | Needs final choice | Compare weekly ratio and weekly residual models; use the more stable one. |
| Distribution method | Needs final choice | Use empirical bootstrap as baseline; compare KDE and gamma benchmark. |
| Lost sales vs. backorder | Recommended | Use lost sales for main model. |
| Holding cost | Needs unit-cost decision | Use actual unit cost if available; otherwise use normalized cost $c=1$. |
| Optimization method | Fixed | Use two-stage grid search as main method; local search as experimental comparison. |
| Validation method | Fixed | Use Monte Carlo validation and historical weekly rolling backtest. |

---

## 28. Final Summary

This revised version uses **weekly demand only**. The weekly forecast $\hat{D}_w$ is treated as the expected demand path, while weekly forecast ratios or weekly residuals represent uncertainty. Simulated weekly demand paths are generated from this uncertainty and then converted into weekly risk-period demand.

The lead time is fixed at:

$$
L=1 \text{ week}
$$

The review period is fixed at:

$$
R=1 \text{ week}
$$

Therefore:

- For GROCERY I and BEVERAGES under $(s,Q)$, the risk period is one week:

  $$
  \tau=L=1
  $$

- For CLEANING under $(R,S)$, the risk period is two weeks:

  $$
  \tau=R+L=2
  $$

The main optimization model is simulation-based. It evaluates candidate weekly inventory policies, rejects candidates that fail the fill-rate constraint, and selects the feasible policy with the lowest cost.

The analytical gamma model remains useful as a benchmark. The shifted gamma using weekly $d_{min}$ is retained, but it should be compared with alternative shift values such as $0$ and $P_1(D_w)$.

The plan is now aligned with weekly demand, deterministic one-week lead time, and one-week review period.
