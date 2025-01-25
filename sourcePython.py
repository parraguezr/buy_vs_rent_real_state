# %% [markdown]
# # Rent vs. Buy Financial Comparison
# 
# This script analyzes the long-term financial implications of renting versus buying a home over a 30-year period. It accepts user-defined inputs (e.g., purchase price, mortgage rate, rent, property taxes, etc.), then calculates and compares the cumulative costs and final net position for each scenario. The notebook also produces tables and charts for clarity, allowing you to see how annual costs and home equity evolve over time.

# %% [markdown]
# ## Cell 1: Setup & Imports
# 
# Explanation:
# This cell imports the necessary libraries for data handling and visualization.
# `pandas` is used for DataFrame manipulations.
# `numpy` is used for numeric operations.
# `matplotlib` is for plotting within the notebook.

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

%matplotlib inline

# %% [markdown]
# ## Cell 2: Input Parameters
# 
# Explanation:
# This dictionary centralizes all the assumptions needed:
# - General parameters like inflation rate, savings rate, analysis years.
# - Rent parameters (current monthly rent).
# - Buy parameters (purchase price, downpayment, closing costs, etc.).
# - Selling assumptions like agent commission.
# 
# We will use these values throughout the calculations.

# %%
inputs = {
    "general": {
        "inflation_rate": 0.025,            # X% yearly inflation for certain costs
        "savings_interest_rate": 0.035,     # Nominal X% annual return on savings/investments
        "analysis_years": 30,              # Typically matches mortgage term
        "house_appreciation_rate": 0.025,  # Nominal X% annual house price growth
        "rent_increase_rate": 0.015         # Nominal X% annual rent increase
    },
    "rent": {
        "current_monthly_rent": 17654.00,  # X kr. monthly
        "annual_renters_insurance": 0.0    # Adjust if you have renter's insurance
    },
    "buy": {
        "cash_price": 6200000.00,      # X kr.
        "downpayment": 1200000.00,         # X kr.
        "closing_costs": 200000.00,        # X kr. (not affected by inflation)
        "mortgage_rate": 0.0503,            # X% annual
        "mortgage_term_years": 30,         # X years
        
        # Property tax rates
        "property_value_tax_rate_below_9200000": 0.0051,  # 0.51% for value up to 9,200,000 DKK
        "property_value_tax_rate_above_9200000": 0.014,   # 1.4% for value exceeding 9,200,000 DKK
        "land_tax_rate": 0.0051,                          # % depends on municipality for land value. See https://www.vurderingsportalen.dk/ejerbolig/boligskat/forstaa-din-boligskat/grundskyld/ and https://www.vurderingsportalen.dk/ejerbolig/boligskat/forstaa-din-boligskat/grundskyld/kommunale-grundskyldspromiller-fra-2024-til-2028/
        
        # Tax authority valuations
        "tax_authority_property_value": 6822000.00,      # Tax authority total valuation of the property
        "tax_authority_land_value": 3869000.00,          # Tax authority total valuation of the land
        "annual_revaluation_rate": 0.015,                # Annual revaluation rate of the house valuation by the tax authority
        
        # Base amounts (year 1); inflated each year by 'inflation_rate'
        "base_insurance": 30000.0,         # X kr. in year 1
        "base_maintenance": 5000.0,      # X kr. in year 1
        "base_renovations": 10000.0,       # X kr. in year 1
        "community_ownership_cost": 5609.0, # X kr. per month (subject to inflation)
        
        "monthly_car_lease": 0.0,          # X kr. per month (affected by inflation)
        
        # Mortgage interest tax deduction
        "interest_deduction_rate": 0.33    # X%
    },
    "selling": {
        "agent_commission_rate": 0.02,     # X% of final sale price
        "capital_gains_tax_rate": 0.00     # X% if not applicable
    }
}


# %% [markdown]
# ## Cell 3: Utility Functions
# 
# Explanation:
# These helper functions handle repeated calculations, such as:
# - Monthly mortgage payment via an annuity formula.
# - Yearly compounding for rent increases and house appreciation.
# - Inflation compounding for various costs.
# 

# %%
def calculate_monthly_mortgage_payment(principal, annual_interest_rate, years):
    """
    Computes the monthly mortgage payment using the standard
    annuity formula:
    P = (r * PV) / (1 - (1 + r)^(-n))
    where r = monthly_interest_rate, n = total months.
    """
    monthly_rate = annual_interest_rate / 12
    num_payments = years * 12
    if monthly_rate == 0:
        return principal / num_payments
    payment = principal * (monthly_rate / (1 - (1 + monthly_rate) ** (-num_payments)))
    return payment

def apply_rent_increase(initial_rent, rent_increase_rate, year):
    """
    Returns the monthly rent for a given 'year', applying
    annual compounding at 'rent_increase_rate'.
    """
    return initial_rent * ((1 + rent_increase_rate) ** (year - 1))

def apply_house_appreciation(initial_value, appreciation_rate, year):
    """
    Returns the house value for a given 'year',
    applying annual compounding at 'appreciation_rate'.
    """
    return initial_value * ((1 + appreciation_rate) ** (year - 1))

def apply_inflation(base_cost, inflation_rate, year):
    """
    Returns the inflated cost in a given 'year',
    applying annual compounding at 'inflation_rate'.
    """
    return base_cost * ((1 + inflation_rate) ** (year - 1))


# %% [markdown]
# ## Cell 4: Rent Scenario Calculation
# 
# Explanation:
# We create a year-by-year breakdown of rent costs, factoring in:
# - The nominal rent increase rate (1.00%).
# - (Optional) Renters insurance or other fees.
# 

# %%
def calculate_rent_scenario(inputs):
    """
    Calculates the total yearly rent cost, including optional
    renter's insurance. Returns columns:
      year, monthly_rent, annual_rent, renters_insurance, total_rent_cost
    """
    rent_data = []
    years = inputs["general"]["analysis_years"]
    rent_increase_rate = inputs["general"]["rent_increase_rate"]
    current_monthly_rent = inputs["rent"]["current_monthly_rent"]
    annual_renters_insurance = inputs["rent"]["annual_renters_insurance"]
    
    for year in range(1, years + 1):
        monthly_rent_this_year = apply_rent_increase(
            current_monthly_rent, 
            rent_increase_rate, 
            year
        )
        annual_rent = monthly_rent_this_year * 12
        total_rent_cost = annual_rent + annual_renters_insurance
        
        rent_data.append({
            "year": year,
            "monthly_rent": monthly_rent_this_year,
            "annual_rent": annual_rent,
            "renters_insurance": annual_renters_insurance,
            "total_rent_cost": total_rent_cost
        })
    
    return pd.DataFrame(rent_data)

rent_df = calculate_rent_scenario(inputs)
rent_df.head(30)


# %% [markdown]
# ## Cell 5: Buy Scenario Calculation
# 
# Explanation:
# This simulates:
# 1. A monthly mortgage amortization to track interest vs. principal.
# 2. Yearly property tax (1.48% of the current house value).
# 3. House appreciation at 2.50% annually.
# 4. Insurance, maintenance, and renovations inflated by 2.00%.
# 5. Mortgage interest tax deduction at 33%.
# 6. Produces a year-by-year DataFrame of costs and final net equity.
# 

# %%
def calculate_buy_scenario(inputs):
    purchase_price = inputs["buy"]["cash_price"]
    downpayment = inputs["buy"]["downpayment"]
    closing_costs = inputs["buy"]["closing_costs"]  # one-time upfront cost
    annual_interest_rate = inputs["buy"]["mortgage_rate"]
    mortgage_term = inputs["buy"]["mortgage_term_years"]
    
    base_insurance = inputs["buy"]["base_insurance"]
    base_maintenance = inputs["buy"]["base_maintenance"]
    base_renovations = inputs["buy"]["base_renovations"]
    community_ownership_cost = inputs["buy"]["community_ownership_cost"]
    
    interest_deduction_rate = inputs["buy"]["interest_deduction_rate"]
    monthly_car_lease = inputs["buy"]["monthly_car_lease"]
    
    # General parameters
    analysis_years = inputs["general"]["analysis_years"]
    inflation_rate = inputs["general"]["inflation_rate"]
    appreciation_rate = inputs["general"]["house_appreciation_rate"]
    
    # Property tax rates
    property_value_tax_rate_below_9200000 = inputs["buy"]["property_value_tax_rate_below_9200000"]
    property_value_tax_rate_above_9200000 = inputs["buy"]["property_value_tax_rate_above_9200000"]
    land_tax_rate = inputs["buy"]["land_tax_rate"]
    
    # Tax authority valuations
    tax_authority_property_value = inputs["buy"]["tax_authority_property_value"]
    tax_authority_land_value = inputs["buy"]["tax_authority_land_value"]
    annual_revaluation_rate = inputs["buy"]["annual_revaluation_rate"]
    
    # Mortgage
    loan_amount = purchase_price - downpayment
    monthly_payment = calculate_monthly_mortgage_payment(
        loan_amount, annual_interest_rate, mortgage_term
    )
    
    mortgage_balance = loan_amount
    buy_data = []
    
    # Month-by-month schedule
    monthly_records = []
    total_months = mortgage_term * 12
    
    for m in range(1, total_months + 1):
        monthly_interest = mortgage_balance * (annual_interest_rate / 12)
        monthly_principal = monthly_payment - monthly_interest
        
        mortgage_balance -= monthly_principal
        mortgage_balance = max(mortgage_balance, 0)  # avoid negative
        
        monthly_records.append({
            "month": m,
            "interest_paid": monthly_interest,
            "principal_paid": monthly_principal,
            "mortgage_balance": mortgage_balance
        })
    
    monthly_df = pd.DataFrame(monthly_records)
    monthly_df["year"] = ((monthly_df["month"] - 1) // 12) + 1
    
    house_value_start = purchase_price
    
    for year in range(1, analysis_years + 1):
        year_df = monthly_df[monthly_df["year"] == year]
        
        if len(year_df) == 0:
            # Mortgage paid off before this year
            interest_paid_this_year = 0.0
            principal_paid_this_year = 0.0
            mortgage_balance_end = 0.0
        else:
            interest_paid_this_year = year_df["interest_paid"].sum()
            principal_paid_this_year = year_df["principal_paid"].sum()
            mortgage_balance_end = year_df["mortgage_balance"].iloc[-1]
        
        # House value start and end of year
        if year == 1:
            house_value_start_year = house_value_start
        else:
            house_value_start_year = buy_data[-1]["house_value_end"]
        
        house_value_end_year = house_value_start_year * (1 + appreciation_rate)
        
        # Property value tax calculation
        taxable_value = tax_authority_property_value * 0.8
        if taxable_value <= 9200000:
            property_value_tax_this_year = taxable_value * property_value_tax_rate_below_9200000
        else:
            property_value_tax_this_year = (9200000 * property_value_tax_rate_below_9200000) + \
                                           ((taxable_value - 9200000) * property_value_tax_rate_above_9200000)
        
        # Land tax calculation (updated)
        taxable_land_value = tax_authority_land_value * (1 - 0.20)
        land_tax_this_year = taxable_land_value * land_tax_rate
        
        # Apply inflation to insurance, maintenance, renovations, community ownership cost, and car lease
        insurance_this_year = apply_inflation(base_insurance, inflation_rate, year)
        maintenance_this_year = apply_inflation(base_maintenance, inflation_rate, year)
        renovations_this_year = apply_inflation(base_renovations, inflation_rate, year)
        community_ownership_cost_this_year = apply_inflation(community_ownership_cost * 12, inflation_rate, year)
        car_lease_this_year = apply_inflation(monthly_car_lease * 12, inflation_rate, year)
        
        # Interest deduction
        net_interest_paid_this_year = interest_paid_this_year * (1 - interest_deduction_rate)
        
        total_annual_outflow = (net_interest_paid_this_year
                                + principal_paid_this_year
                                + property_value_tax_this_year
                                + land_tax_this_year
                                + insurance_this_year
                                + maintenance_this_year
                                + renovations_this_year
                                + community_ownership_cost_this_year
                                + car_lease_this_year)
        
        net_equity_end = house_value_end_year - mortgage_balance_end
        
        buy_data.append({
            "year": year,
            "interest_paid": net_interest_paid_this_year,
            "principal_paid": principal_paid_this_year,
            "property_value_tax": property_value_tax_this_year,
            "land_tax": land_tax_this_year,
            "insurance": insurance_this_year,
            "maintenance": maintenance_this_year,
            "renovations": renovations_this_year,
            "community_ownership_cost": community_ownership_cost_this_year,
            "car_lease": car_lease_this_year,
            "total_outflow": total_annual_outflow,
            "mortgage_balance_end": mortgage_balance_end,
            "house_value_start": house_value_start_year,
            "house_value_end": house_value_end_year,
            "net_equity_end": net_equity_end
        })
        
        # Revalue the property and land for the next year
        tax_authority_property_value *= (1 + annual_revaluation_rate)
        tax_authority_land_value *= (1 + annual_revaluation_rate)
    
    return pd.DataFrame(buy_data)



buy_df = calculate_buy_scenario(inputs)
buy_df.head(30)


# %% [markdown]
# ## Cell 6: Enhanced Rent Scenario (Invest the Difference)
# 
# Explanation:
# Simulates investing the unspent downpayment + closing costs, 
# plus any annual difference in outflows (if renting is cheaper, deposit that difference; if it's more expensive, withdraw it).
# We apply a 3.00% annual return on the investment.
# 

# %%
def calculate_rent_investment_scenario(inputs, rent_df, buy_df):
    """
    Tracks how the renting scenario invests the difference in costs plus
    the initial downpayment+closing that are NOT spent when not buying.
    
    Returns columns:
      year, rent_outflow, buy_outflow, difference, investment_start,
      investment_end, final_rent_net_worth
    """
    
    merged = pd.DataFrame({
        "year": rent_df["year"],
        "rent_outflow": rent_df["total_rent_cost"],
        "buy_outflow": buy_df["total_outflow"]
    })
    
    initial_investment = inputs["buy"]["downpayment"] + inputs["buy"]["closing_costs"]
    savings_rate = inputs["general"]["savings_interest_rate"]
    analysis_years = inputs["general"]["analysis_years"]
    
    rent_invest_data = []
    investment_balance = initial_investment
    
    for year in range(1, analysis_years + 1):
        row = merged[merged["year"] == year].iloc[0]
        
        rent_cost = row["rent_outflow"]
        buy_cost = row["buy_outflow"]
        
        # difference > 0 => deposit (rent is cheaper)
        difference = buy_cost - rent_cost
        
        investment_start = investment_balance
        investment_after_diff = investment_start + difference
        
        # Apply annual interest
        investment_end = investment_after_diff * (1 + savings_rate)
        
        investment_balance = investment_end
        
        rent_invest_data.append({
            "year": year,
            "rent_outflow": rent_cost,
            "buy_outflow": buy_cost,
            "difference": difference,
            "investment_start": investment_start,
            "investment_end": investment_end
        })
    
    df_rent_invest = pd.DataFrame(rent_invest_data)
    df_rent_invest["final_rent_net_worth"] = df_rent_invest["investment_end"].iloc[-1]
    return df_rent_invest

rent_invest_df = calculate_rent_investment_scenario(inputs, rent_df, buy_df)
rent_invest_df.head(30)


# %% [markdown]
# ## Cell 7: Comparison & Summary
# 
# Explanation:
# We aggregate the total outflow for rent vs. buy, then compute:
# - Final net worth for renting = final investment balance.
# - Final net worth for buying = net equity in the property (house value - mortgage) minus selling costs (agent commission, CGT).
# The function returns a dictionary of key results.
# 

# %%
def compare_scenarios(rent_df, buy_df, rent_invest_df, inputs):
    total_rent_outflow = rent_df["total_rent_cost"].sum()
    final_rent_net_worth = rent_invest_df["final_rent_net_worth"].iloc[-1]
    
    total_buy_outflow = buy_df["total_outflow"].sum()
    
    # Final net equity for buying
    last_year = inputs["general"]["analysis_years"]
    final_buy_row = buy_df[buy_df["year"] == last_year].iloc[0]
    final_home_value = final_buy_row["house_value_end"]
    final_mortgage_balance = final_buy_row["mortgage_balance_end"]
    
    raw_equity = final_home_value - final_mortgage_balance
    
    # Selling costs
    commission_rate = inputs["selling"]["agent_commission_rate"]
    capital_gains_rate = inputs["selling"]["capital_gains_tax_rate"]
    
    agent_commission = final_home_value * commission_rate
    purchase_price = inputs["buy"]["cash_price"]
    capital_gains = max(final_home_value - purchase_price, 0)
    cgt = capital_gains * capital_gains_rate
    
    final_net_equity_buying = raw_equity - agent_commission - cgt
    
    difference_in_net_worth = final_net_equity_buying - final_rent_net_worth
    
    return {
        "total_rent_outflow": total_rent_outflow,
        "final_rent_net_worth": final_rent_net_worth,
        "total_buy_outflow": total_buy_outflow,
        "final_net_equity_buying": final_net_equity_buying,
        "difference_in_net_worth": difference_in_net_worth
    }

comparison_result = compare_scenarios(rent_df, buy_df, rent_invest_df, inputs)
comparison_result


# %% [markdown]
# ## Cell 8: Visualizations
# 
# Explanation:
# We create plots to visualize:
# 1. Annual outflow (Rent vs. Buy).
# 2. Investment balance over time for the Rent scenario.
# 3. Net equity progression over time for the Buy scenario.
# 

# %%
def plot_scenarios(rent_df, buy_df, rent_invest_df):
    plt.figure(figsize=(10, 5))
    plt.plot(rent_df["year"], rent_df["total_rent_cost"], label="Rent Annual Outflow", marker='o')
    plt.plot(buy_df["year"], buy_df["total_outflow"], label="Buy Annual Outflow", marker='o')
    plt.xlabel("Year")
    plt.ylabel("Cost (DKK)")
    plt.title("Annual Outflow: Renting vs. Buying")
    plt.legend()
    plt.grid(True)
    plt.show()
    
    plt.figure(figsize=(10, 5))
    plt.plot(rent_invest_df["year"], rent_invest_df["investment_end"], label="Rent Investment Balance", marker='o', color='orange')
    plt.xlabel("Year")
    plt.ylabel("DKK")
    plt.title("Investment Growth When Renting")
    plt.legend()
    plt.grid(True)
    plt.show()
    
    plt.figure(figsize=(10, 5))
    plt.plot(buy_df["year"], buy_df["net_equity_end"], label="Home Equity (Buy)", marker='o', color='green')
    plt.xlabel("Year")
    plt.ylabel("DKK")
    plt.title("Net Equity Over Time (Buying)")
    plt.legend()
    plt.grid(True)
    plt.show()

plot_scenarios(rent_df, buy_df, rent_invest_df)


# %% [markdown]
# ## Additional Visualizations
# 
# Explanation:
# This cell provides a set of extra plots to deepen the year-by-year comparison
# between renting and buying. It includes:
#  
#  1. **Stacked Bar Chart** of the Buy Scenario's cost breakdown.
#  2. **Stacked Bar Chart** of the Rent Scenario's cost breakdown (if desired).
#  3. **Mortgage Balance vs. House Value** (Buy scenario).
#  4. **Difference in Net Worth** (Buy vs. Rent) each year.
#  5. **Cumulative Outflow** for both Rent and Buy.
#  
#  Assumptions:
#  - We already have `rent_df`, `buy_df`, and `rent_invest_df` DataFrames in scope.
#  - `rent_invest_df` models "Invest the Difference" so we can compare net worth accurately.
#  - Each DataFrame has a 'year' column that aligns (1..analysis_years).
#  - For the difference in net worth: we assume `buy_df["net_equity_end"]` vs. `rent_invest_df["investment_end"]`.

# %%
import pandas as pd
import matplotlib.pyplot as plt

def plot_additional_comparisons_separate_principal(rent_df, buy_df, rent_invest_df):
    """
    Produces a series of extra charts:
      1. Stacked bar of buy-scenario yearly costs (principal, interest, property tax, etc.).
      2. (Optional) Stacked bar of rent-scenario yearly costs.
      3. Mortgage Balance vs. House Value over time (Buy).
      4. Difference in Net Worth (Buy - Rent) each year.
      5. Cumulative Outflow (Rent vs. Buy).
      6. Stacked bar of buy-scenario average monthly costs for the first 5 years.
    """

    # --- Debug Info (optional) ---
    print("Buy DF (first few rows):")
    print(buy_df.head(), "\n")
    print("Rent DF (first few rows):")
    print(rent_df.head(), "\n")
    print("Rent Invest DF (first few rows):")
    print(rent_invest_df.head(), "\n")

    # 1) Stacked Bar Chart: Buy Scenario Cost Breakdown (Separate Principal & Interest)
    # --------------------------------------------------------------------------------
    cost_components_buy = pd.DataFrame({
        'year': buy_df['year'],
        'Principal': buy_df['principal_paid'],
        'Interest': buy_df['interest_paid'],
        'Property Tax': buy_df['property_value_tax'],
        'Land Tax': buy_df['land_tax'],
        'Insurance': buy_df['insurance'],
        'Maintenance': buy_df['maintenance'],
        'Renovations': buy_df['renovations'],
        'Community Ownership Cost': buy_df['community_ownership_cost'],
    })
    
    cost_components_buy.set_index('year', inplace=True)

    # Debug check
    print("Buy Cost Components DF:")
    print(cost_components_buy.head(), "\n")

    plt.figure(figsize=(10, 6))
    cost_components_buy.plot(kind='bar', stacked=True)
    plt.title("Buy Scenario: Yearly Cost Breakdown (Stacked) - Principal vs. Interest")
    plt.xlabel("Year")
    plt.ylabel("Cost (DKK)")
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
    plt.tight_layout()
    plt.show()

    # 2) Stacked Bar Chart: Rent Scenario Cost Breakdown
    # --------------------------------------------------
    cost_components_rent = pd.DataFrame({
        'year': rent_df['year'],
        'Rent': rent_df['annual_rent'],
        'Renter Insurance': rent_df['renters_insurance']
    })
    cost_components_rent.set_index('year', inplace=True)

    # Debug check
    print("Rent Cost Components DF:")
    print(cost_components_rent.head(), "\n")

    plt.figure(figsize=(10, 6))
    cost_components_rent.plot(kind='bar', stacked=True, color=['#1f77b4', '#ff7f0e'])
    plt.title("Rent Scenario: Yearly Cost Breakdown (Stacked)")
    plt.xlabel("Year")
    plt.ylabel("Cost (DKK)")
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

    # 3) Mortgage Balance vs. House Value Over Time (Buy Scenario)
    # ------------------------------------------------------------
    plt.figure(figsize=(10, 6))
    plt.plot(buy_df["year"], buy_df["mortgage_balance_end"], 
             label="Mortgage Balance", marker='o', color='red')
    plt.plot(buy_df["year"], buy_df["house_value_end"], 
             label="House Value", marker='o', color='green')
    plt.title("Mortgage Balance vs. House Value Over Time (Buy)")
    plt.xlabel("Year")
    plt.ylabel("DKK")
    plt.grid(True)
    plt.legend()
    plt.show()

    # 4) Difference in Net Worth Each Year (Buy - Rent)
    # --------------------------------------------------
    diff_df = pd.DataFrame({
        'year': buy_df['year'],
        'net_equity_buy': buy_df['net_equity_end'],
        'net_worth_rent': rent_invest_df['investment_end']
    })
    diff_df['difference'] = diff_df['net_equity_buy'] - diff_df['net_worth_rent']

    print("Difference DF (first few rows):")
    print(diff_df.head(), "\n")

    plt.figure(figsize=(10, 6))
    plt.plot(diff_df["year"], diff_df["difference"], 
             marker='o', color='purple', label="Net Worth Difference (Buy - Rent)")
    plt.title("Difference in Net Worth Over Time")
    plt.xlabel("Year")
    plt.ylabel("DKK")
    plt.grid(True)
    plt.axhline(y=0, color='black', linestyle='--')
    plt.legend()
    plt.show()

    # 5) Cumulative Outflow Comparison (Rent vs. Buy)
    # -----------------------------------------------
    # We'll sum up the yearly outflows for each scenario and plot them cumulatively.
    rent_df['cumulative_rent_outflow'] = rent_df['total_rent_cost'].cumsum()
    buy_df['cumulative_buy_outflow'] = buy_df['total_outflow'].cumsum()

    plt.figure(figsize=(10, 6))
    plt.plot(rent_df["year"], rent_df["cumulative_rent_outflow"], 
             label="Cumulative Rent Outflow", marker='o')
    plt.plot(buy_df["year"], buy_df["cumulative_buy_outflow"], 
             label="Cumulative Buy Outflow", marker='o')
    plt.title("Cumulative Outflow: Renting vs. Buying")
    plt.xlabel("Year")
    plt.ylabel("Total Outflow (DKK)")
    plt.grid(True)
    plt.legend()
    plt.show()

    # 6) Stacked Bar Chart: Buy Scenario Average Monthly Cost Breakdown (First 5 Years)
    # ---------------------------------------------------------------------------------
    cost_components_buy_monthly = cost_components_buy.loc[cost_components_buy.index <= 3].div(12)
    
    plt.figure(figsize=(20, 45)) 
    ax = cost_components_buy_monthly.plot(kind='bar', stacked=True)
    plt.title("Buy Scenario: Average Monthly Cost Breakdown (First 3 Years)")
    plt.xlabel("Year")
    plt.ylabel("Cost (DKK)")
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
    
    # Add DKK values for each segment
    for container in ax.containers:
        ax.bar_label(container, fmt='%.0f', label_type='center')
    
    plt.tight_layout()
    plt.show()

# To use, confirm that your data is valid and then call:
plot_additional_comparisons_separate_principal(rent_df, buy_df, rent_invest_df)


# %% [markdown]
# ## Cell 9: Conclusions
# 
# Explanation:
# We print a summary of final outflows and net worth in each scenario, 
# and state which scenario yields a higher final net worth after 30 years.
# 

# %%
print("=== RENT VS BUY COMPARISON (THOROUGH) ===")

print(f"Total Renting Outflow: {comparison_result['total_rent_outflow']:.2f} DKK")
print(f"Final Net Worth (Rent + Investment): {comparison_result['final_rent_net_worth']:.2f} DKK")

print(f"Total Buying Outflow: {comparison_result['total_buy_outflow']:.2f} DKK")
print(f"Final Net Equity (Buying, after sale costs): {comparison_result['final_net_equity_buying']:.2f} DKK")

diff = comparison_result["difference_in_net_worth"]
if diff > 0:
    print(f"Buying yields {abs(diff):.2f} DKK more net worth than Renting.")
elif diff < 0:
    print(f"Renting yields {abs(diff):.2f} DKK more net worth than Buying.")
else:
    print("Both scenarios end up with the same net worth!")



