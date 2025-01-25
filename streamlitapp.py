import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 1) Streamlit Page Config ---
st.set_page_config(
    page_title="Rent vs Buy Comparison",
    layout="centered",  # Could also use "wide"
    initial_sidebar_state="expanded"
)


# --- 2) Utility Functions (same as in your notebook) ---
def calculate_monthly_mortgage_payment(principal, annual_interest_rate, years):
    """Computes the monthly mortgage payment using the standard annuity formula."""
    monthly_rate = annual_interest_rate / 12
    num_payments = years * 12
    if monthly_rate == 0:
        return principal / num_payments
    payment = principal * (monthly_rate / (1 - (1 + monthly_rate) ** (-num_payments)))
    return payment

def apply_rent_increase(initial_rent, rent_increase_rate, year):
    """Returns monthly rent for a given year, applying annual compounding."""
    return initial_rent * ((1 + rent_increase_rate) ** (year - 1))

def apply_house_appreciation(initial_value, appreciation_rate, year):
    """Returns house value for a given year, applying annual compounding."""
    return initial_value * ((1 + appreciation_rate) ** (year - 1))

def apply_inflation(base_cost, inflation_rate, year):
    """Returns inflated cost for a given year, using annual compounding."""
    return base_cost * ((1 + inflation_rate) ** (year - 1))


def calculate_rent_scenario(inputs):
    """Builds a year-by-year DataFrame of rent costs (including insurance)."""
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


def calculate_buy_scenario(inputs):
    """Builds a year-by-year DataFrame of homeownership costs and equity."""
    purchase_price = inputs["buy"]["cash_price"]
    downpayment = inputs["buy"]["downpayment"]
    closing_costs = inputs["buy"]["closing_costs"]  # one-time upfront
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
        taxable_value = tax_authority_property_value * 0.8  # example logic
        if taxable_value <= 9200000:
            property_value_tax_this_year = taxable_value * property_value_tax_rate_below_9200000
        else:
            property_value_tax_this_year = (
                9200000 * property_value_tax_rate_below_9200000
                + (taxable_value - 9200000) * property_value_tax_rate_above_9200000
            )
        
        # Land tax calculation
        taxable_land_value = tax_authority_land_value * (1 - 0.20)
        land_tax_this_year = taxable_land_value * land_tax_rate
        
        # Apply inflation to certain costs
        insurance_this_year = apply_inflation(base_insurance, inflation_rate, year)
        maintenance_this_year = apply_inflation(base_maintenance, inflation_rate, year)
        renovations_this_year = apply_inflation(base_renovations, inflation_rate, year)
        community_ownership_cost_this_year = apply_inflation(
            community_ownership_cost * 12, inflation_rate, year
        )
        car_lease_this_year = apply_inflation(monthly_car_lease * 12, inflation_rate, year)
        
        # Interest deduction
        net_interest_paid_this_year = interest_paid_this_year * (1 - interest_deduction_rate)
        
        total_annual_outflow = (
            net_interest_paid_this_year
            + principal_paid_this_year
            + property_value_tax_this_year
            + land_tax_this_year
            + insurance_this_year
            + maintenance_this_year
            + renovations_this_year
            + community_ownership_cost_this_year
            + car_lease_this_year
        )
        
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
        
        # Revalue the property for next year
        tax_authority_property_value *= (1 + annual_revaluation_rate)
        tax_authority_land_value *= (1 + annual_revaluation_rate)
    
    return pd.DataFrame(buy_data)


def calculate_rent_investment_scenario(inputs, rent_df, buy_df):
    """
    Simulates investing the downpayment+closing costs plus 
    any annual cost difference (if renting is cheaper).
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
        
        # difference = how much cheaper (or more expensive) renting is vs buying
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


def compare_scenarios(rent_df, buy_df, rent_invest_df, inputs):
    """
    Summarizes total outflow for rent vs. buy,
    and final net worth in each scenario.
    """
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


# --- 3) Streamlit App Layout ---
st.title("Rent vs. Buy Financial Comparison")
st.markdown("""
This app analyzes the long-term financial implications of **renting** vs. **buying** a home over a user-defined period.
You can adjust the assumptions in the sidebar, and the app will re-run the calculations.
""")

# Sidebar for Key Parameters
st.sidebar.header("General Assumptions")
analysis_years = st.sidebar.number_input("Analysis Term (years)", min_value=1, max_value=50, value=30)
inflation_rate = st.sidebar.slider("Annual Inflation Rate", min_value=0.0, max_value=0.1, value=0.025, step=0.001)
savings_interest_rate = st.sidebar.slider("Savings/Investment Rate", min_value=0.0, max_value=0.1, value=0.035, step=0.001)
house_appreciation_rate = st.sidebar.slider("House Appreciation Rate", min_value=0.0, max_value=0.1, value=0.025, step=0.001)
rent_increase_rate = st.sidebar.slider("Rent Increase Rate", min_value=0.0, max_value=0.1, value=0.015, step=0.001)

st.sidebar.header("Rent Scenario")
current_monthly_rent = st.sidebar.number_input("Current Monthly Rent (DKK)", value=17654, step=1000)
annual_renters_insurance = st.sidebar.number_input("Annual Renter's Insurance (DKK)", value=0, step=500)

st.sidebar.header("Buy Scenario")
cash_price = st.sidebar.number_input("Purchase Price (DKK)", value=6200000, step=100000)
downpayment = st.sidebar.number_input("Downpayment (DKK)", value=1200000, step=100000)
closing_costs = st.sidebar.number_input("Closing Costs (DKK)", value=200000, step=50000)
mortgage_rate = st.sidebar.slider("Mortgage Interest Rate", min_value=0.0, max_value=0.15, value=0.0503, step=0.0001)
mortgage_term_years = st.sidebar.number_input("Mortgage Term (years)", value=30)
property_value_tax_below_9200k = st.sidebar.number_input("Property Value Tax Rate (<= 9,200,000)", value=0.0051, step=0.0001, format="%.4f")
property_value_tax_above_9200k = st.sidebar.number_input("Property Value Tax Rate (> 9,200,000)", value=0.0140, step=0.0001, format="%.4f")
land_tax_rate = st.sidebar.number_input("Land Tax Rate", value=0.0051, step=0.0001, format="%.4f")
tax_authority_property_value = st.sidebar.number_input("Tax Authority's Property Valuation (DKK)", value=6822000, step=100000)
tax_authority_land_value = st.sidebar.number_input("Tax Authority's Land Valuation (DKK)", value=3869000, step=100000)
annual_revaluation_rate = st.sidebar.slider("Annual Revaluation Rate (Tax Valuation)", min_value=0.0, max_value=0.05, value=0.015, step=0.001)
interest_deduction_rate = st.sidebar.slider("Mortgage Interest Deduction Rate", min_value=0.0, max_value=0.5, value=0.33, step=0.01)

st.sidebar.header("Other Yearly Costs (Buy)")
base_insurance = st.sidebar.number_input("Home Insurance (Year 1)", value=30000, step=1000)
base_maintenance = st.sidebar.number_input("Maintenance (Year 1)", value=5000, step=1000)
base_renovations = st.sidebar.number_input("Renovations (Year 1)", value=10000, step=1000)
community_ownership_cost = st.sidebar.number_input("Monthly Community Ownership Fee (Year 1)", value=5609, step=500)
monthly_car_lease = st.sidebar.number_input("Monthly Car Lease (if any)", value=0, step=500)

st.sidebar.header("Selling Assumptions")
agent_commission_rate = st.sidebar.slider("Agent Commission Rate", min_value=0.0, max_value=0.1, value=0.02, step=0.001)
capital_gains_tax_rate = st.sidebar.slider("Capital Gains Tax Rate", min_value=0.0, max_value=0.5, value=0.0, step=0.01)


# --- 4) Build 'inputs' Dictionary from Sidebar ---
inputs = {
    "general": {
        "inflation_rate": inflation_rate,
        "savings_interest_rate": savings_interest_rate,
        "analysis_years": int(analysis_years),
        "house_appreciation_rate": house_appreciation_rate,
        "rent_increase_rate": rent_increase_rate
    },
    "rent": {
        "current_monthly_rent": current_monthly_rent,
        "annual_renters_insurance": annual_renters_insurance
    },
    "buy": {
        "cash_price": cash_price,
        "downpayment": downpayment,
        "closing_costs": closing_costs,
        "mortgage_rate": mortgage_rate,
        "mortgage_term_years": int(mortgage_term_years),
        
        "property_value_tax_rate_below_9200000": property_value_tax_below_9200k,
        "property_value_tax_rate_above_9200000": property_value_tax_above_9200k,
        "land_tax_rate": land_tax_rate,
        
        "tax_authority_property_value": tax_authority_property_value,
        "tax_authority_land_value": tax_authority_land_value,
        "annual_revaluation_rate": annual_revaluation_rate,
        
        "base_insurance": base_insurance,
        "base_maintenance": base_maintenance,
        "base_renovations": base_renovations,
        "community_ownership_cost": community_ownership_cost,
        "monthly_car_lease": monthly_car_lease,
        
        "interest_deduction_rate": interest_deduction_rate
    },
    "selling": {
        "agent_commission_rate": agent_commission_rate,
        "capital_gains_tax_rate": capital_gains_tax_rate
    }
}


# --- 5) Run Calculations ---
rent_df = calculate_rent_scenario(inputs)
buy_df = calculate_buy_scenario(inputs)
rent_invest_df = calculate_rent_investment_scenario(inputs, rent_df, buy_df)
comparison_result = compare_scenarios(rent_df, buy_df, rent_invest_df, inputs)


# --- 6) Display Results ---
st.subheader("Rent Scenario (Year-by-Year)")
st.dataframe(rent_df.style.format("{:,.2f}"))

st.subheader("Buy Scenario (Year-by-Year)")
st.dataframe(buy_df.style.format("{:,.2f}"))

st.subheader("Rent + Invest Scenario (Year-by-Year)")
st.dataframe(rent_invest_df.style.format("{:,.2f}"))

st.subheader("Overall Comparison & Summary")
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Rent Outflow", f"{comparison_result['total_rent_outflow']:,.0f} DKK")
    st.metric("Final Net Worth (Rent + Investment)", 
              f"{comparison_result['final_rent_net_worth']:,.0f} DKK")

with col2:
    st.metric("Total Buy Outflow", f"{comparison_result['total_buy_outflow']:,.0f} DKK")
    st.metric("Final Net Equity (Buying)", 
              f"{comparison_result['final_net_equity_buying']:,.0f} DKK")

difference = comparison_result["difference_in_net_worth"]
if difference > 0:
    st.success(
        f"**Buying** yields **{abs(difference):,.0f} DKK** **more** net worth than Renting at the end of {analysis_years} years."
    )
elif difference < 0:
    st.warning(
        f"**Renting** yields **{abs(difference):,.0f} DKK** **more** net worth than Buying at the end of {analysis_years} years."
    )
else:
    st.info("Both scenarios end up with exactly the same net worth!")


# --- 7) Plots ---
st.subheader("Visual Comparisons")

fig1, ax1 = plt.subplots(figsize=(8, 4))
ax1.plot(rent_df["year"], rent_df["total_rent_cost"], label="Rent Annual Outflow", marker='o')
ax1.plot(buy_df["year"], buy_df["total_outflow"], label="Buy Annual Outflow", marker='o')
ax1.set_xlabel("Year")
ax1.set_ylabel("Cost (DKK)")
ax1.set_title("Annual Outflow: Renting vs. Buying")
ax1.legend()
ax1.grid(True)
st.pyplot(fig1)

fig2, ax2 = plt.subplots(figsize=(8, 4))
ax2.plot(rent_invest_df["year"], rent_invest_df["investment_end"], 
         label="Rent Investment Balance", marker='o', color='orange')
ax2.set_xlabel("Year")
ax2.set_ylabel("DKK")
ax2.set_title("Investment Growth When Renting")
ax2.legend()
ax2.grid(True)
st.pyplot(fig2)

fig3, ax3 = plt.subplots(figsize=(8, 4))
ax3.plot(buy_df["year"], buy_df["net_equity_end"], label="Home Equity (Buy)", marker='o', color='green')
ax3.set_xlabel("Year")
ax3.set_ylabel("DKK")
ax3.set_title("Net Equity Over Time (Buying)")
ax3.legend()
ax3.grid(True)
st.pyplot(fig3)

# Additional Visualizations
st.subheader("Additional Visual Comparisons")

# 1) Stacked Bar Chart: Buy Scenario Cost Breakdown (Separate Principal & Interest)
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

fig4, ax4 = plt.subplots(figsize=(10, 6))
cost_components_buy.plot(kind='bar', stacked=True, ax=ax4)
ax4.set_title("Buy Scenario: Yearly Cost Breakdown (Stacked) - Principal vs. Interest")
ax4.set_xlabel("Year")
ax4.set_ylabel("Cost (DKK)")
ax4.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
ax4.grid(True)
st.pyplot(fig4)

# 2) Stacked Bar Chart: Rent Scenario Cost Breakdown
cost_components_rent = pd.DataFrame({
    'year': rent_df['year'],
    'Rent': rent_df['annual_rent'],
    'Renter Insurance': rent_df['renters_insurance']
})
cost_components_rent.set_index('year', inplace=True)

fig5, ax5 = plt.subplots(figsize=(10, 6))
cost_components_rent.plot(kind='bar', stacked=True, color=['#1f77b4', '#ff7f0e'], ax=ax5)
ax5.set_title("Rent Scenario: Yearly Cost Breakdown (Stacked)")
ax5.set_xlabel("Year")
ax5.set_ylabel("Cost (DKK)")
ax5.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
ax5.grid(True)
st.pyplot(fig5)

# 3) Mortgage Balance vs. House Value Over Time (Buy Scenario)
fig6, ax6 = plt.subplots(figsize=(10, 6))
ax6.plot(buy_df["year"], buy_df["mortgage_balance_end"], label="Mortgage Balance", marker='o', color='red')
ax6.plot(buy_df["year"], buy_df["house_value_end"], label="House Value", marker='o', color='green')
ax6.set_title("Mortgage Balance vs. House Value Over Time (Buy)")
ax6.set_xlabel("Year")
ax6.set_ylabel("DKK")
ax6.grid(True)
ax6.legend()
st.pyplot(fig6)

# 4) Difference in Net Worth Each Year (Buy - Rent)
diff_df = pd.DataFrame({
    'year': buy_df['year'],
    'net_equity_buy': buy_df['net_equity_end'],
    'net_worth_rent': rent_invest_df['investment_end']
})
diff_df['difference'] = diff_df['net_equity_buy'] - diff_df['net_worth_rent']

fig7, ax7 = plt.subplots(figsize=(10, 6))
ax7.plot(diff_df["year"], diff_df["difference"], marker='o', color='purple', label="Net Worth Difference (Buy - Rent)")
ax7.set_title("Difference in Net Worth Over Time")
ax7.set_xlabel("Year")
ax7.set_ylabel("DKK")
ax7.grid(True)
ax7.axhline(y=0, color='black', linestyle='--')
ax7.legend()
st.pyplot(fig7)

# 5) Cumulative Outflow Comparison (Rent vs. Buy)
rent_df['cumulative_rent_outflow'] = rent_df['total_rent_cost'].cumsum()
buy_df['cumulative_buy_outflow'] = buy_df['total_outflow'].cumsum()

fig8, ax8 = plt.subplots(figsize=(10, 6))
ax8.plot(rent_df["year"], rent_df["cumulative_rent_outflow"], label="Cumulative Rent Outflow", marker='o')
ax8.plot(buy_df["year"], buy_df["cumulative_buy_outflow"], label="Cumulative Buy Outflow", marker='o')
ax8.set_title("Cumulative Outflow: Renting vs. Buying")
ax8.set_xlabel("Year")
ax8.set_ylabel("Total Outflow (DKK)")
ax8.grid(True)
ax8.legend()
st.pyplot(fig8)

# 6) Stacked Bar Chart: Buy Scenario Average Monthly Cost Breakdown (First 3 Years)
cost_components_buy_monthly = cost_components_buy.loc[cost_components_buy.index <= 3].div(12)

fig9, ax9 = plt.subplots(figsize=(10, 6))
cost_components_buy_monthly.plot(kind='bar', stacked=True, ax=ax9)
ax9.set_title("Buy Scenario: Average Monthly Cost Breakdown (First 3 Years)")
ax9.set_xlabel("Year")
ax9.set_ylabel("Cost (DKK)")
ax9.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
ax9.grid(True)
st.pyplot(fig9)

st.write("Adjust the sliders in the sidebar to explore different assumptions!")

