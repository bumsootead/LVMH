"""
Stock Analysis Module for LVMH Stock
- Volatility Analysis
- Yearly Stock Growth Analysis
- Visualization of Volume, Growth, and Volatility
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib
from datetime import datetime

# Load the data
data = pd.read_csv('Data/LV.csv')
data['Date'] = pd.to_datetime(data['Date'])
data = data.sort_values('Date').reset_index(drop=True)

# Remove rows with zero volume (non-trading days)
data = data[data['Volume'] > 0].reset_index(drop=True)

print("=" * 60)
print("LVMH STOCK ANALYSIS")
print("=" * 60)
print(f"Data range: {data['Date'].min()} to {data['Date'].max()}")
print(f"Total trading days: {len(data)}")
print()

# ============================================================
# 1. VOLATILITY ANALYSIS
# ============================================================
print("=" * 60)
print("VOLATILITY ANALYSIS")
print("=" * 60)

# Calculate daily returns
data['Returns'] = data['Close'].pct_change()

# Calculate volatility using rolling standard deviation of returns
# Using 20-day (approximately 1 month) rolling window
data['Volatility_20d'] = data['Returns'].rolling(window=20).std() * np.sqrt(252)  # Annualized

# Also calculate using price range (High - Low) / Close
data['Price_Range'] = (data['High'] - data['Low']) / data['Close']
data['Historical_Volatility'] = data['Price_Range'].rolling(window=20).mean() * np.sqrt(252)

# Calculate average annual volatility per year
data['Year'] = data['Date'].dt.year
annual_volatility = data.groupby('Year')['Volatility_20d'].mean()

print("Annual Volatility by Year (Annualized):")
print("-" * 40)
for year, vol in annual_volatility.items():
    if not pd.isna(vol):
        print(f"  {year}: {vol:.2%}")

# Save volatility analysis
volatility_stats = {
    'mean_volatility': data['Volatility_20d'].mean(),
    'max_volatility': data['Volatility_20d'].max(),
    'min_volatility': data['Volatility_20d'].min(),
    'std_volatility': data['Volatility_20d'].std(),
    'annual_volatility_by_year': annual_volatility.to_dict()
}

print()
print(f"Mean Annualized Volatility: {volatility_stats['mean_volatility']:.2%}")
print(f"Max Annualized Volatility: {volatility_stats['max_volatility']:.2%}")
print(f"Min Annualized Volatility: {volatility_stats['min_volatility']:.2%}")

# Save volatility model/analysis
joblib.dump(volatility_stats, 'volatility_analysis.pkl')
print("\nVolatility analysis saved to volatility_analysis.pkl")

# ============================================================
# 2. YEARLY STOCK GROWTH ANALYSIS
# ============================================================
print()
print("=" * 60)
print("YEARLY STOCK GROWTH ANALYSIS")
print("=" * 60)

# Calculate yearly returns
yearly_data = data.groupby('Year').agg({
    'Open': 'first',
    'Close': 'last',
    'Volume': 'mean',
    'Returns': 'mean'
}).reset_index()

yearly_data['Yearly_Return'] = (yearly_data['Close'] - yearly_data['Open']) / yearly_data['Open']

print("Yearly Stock Performance:")
print("-" * 40)
print(f"{'Year':<10} {'Open':<15} {'Close':<15} {'Growth %':<15}")
print("-" * 40)
for _, row in yearly_data.iterrows():
    if not pd.isna(row['Yearly_Return']):
        print(f"{int(row['Year']):<10} ${row['Open']:<14.2f} ${row['Close']:<14.2f} {row['Yearly_Return']:>+.2%}")

# Calculate cumulative growth
first_price = yearly_data['Open'].iloc[0]
last_price = yearly_data['Close'].iloc[-1]
total_growth = (last_price - first_price) / first_price

print()
print(f"Total Growth (2000-{int(yearly_data['Year'].iloc[-1])}): {total_growth:+.2%}")
print(f"Average Annual Return: {yearly_data['Yearly_Return'].mean():.2%}")

# Save yearly growth analysis
growth_stats = {
    'yearly_returns': yearly_data[['Year', 'Yearly_Return', 'Open', 'Close', 'Volume']].to_dict('records'),
    'total_growth': total_growth,
    'average_annual_return': yearly_data['Yearly_Return'].mean(),
    'best_year': int(yearly_data.loc[yearly_data['Yearly_Return'].idxmax(), 'Year']),
    'worst_year': int(yearly_data.loc[yearly_data['Yearly_Return'].idxmin(), 'Year']),
    'best_return': yearly_data['Yearly_Return'].max(),
    'worst_return': yearly_data['Yearly_Return'].min()
}

joblib.dump(growth_stats, 'growth_analysis.pkl')
print("\nGrowth analysis saved to growth_analysis.pkl")

# ============================================================
# 3. VISUALIZATIONS
# ============================================================
print()
print("=" * 60)
print("GENERATING VISUALIZATIONS")
print("=" * 60)

# Create figure with 3 subplots
fig, axes = plt.subplots(3, 1, figsize=(14, 12))
fig.suptitle('LVMH Stock Analysis', fontsize=16, fontweight='bold')

# Plot 1: Volume Over Time
ax1 = axes[0]
ax1.fill_between(data['Date'], data['Volume'], alpha=0.4, color='blue')
ax1.plot(data['Date'], data['Volume'], color='blue', linewidth=0.5)
ax1.set_title('Trading Volume Over Time', fontsize=12, fontweight='bold')
ax1.set_xlabel('Date')
ax1.set_ylabel('Volume')
ax1.grid(True, alpha=0.3)

# Add yearly average volume line
yearly_volume = data.groupby('Year')['Volume'].mean()
ax1.axhline(y=yearly_volume.mean(), color='red', linestyle='--', 
            label=f'Avg Volume: {yearly_volume.mean():,.0f}')
ax1.legend()

# Plot 2: Yearly Stock Growth
ax2 = axes[1]
years = yearly_data['Year'].dropna()
returns = yearly_data['Yearly_Return'].dropna()
colors = ['green' if r >= 0 else 'red' for r in returns]
bars = ax2.bar(years, returns * 100, color=colors, edgecolor='black', alpha=0.7)
ax2.set_title('Yearly Stock Growth (%)', fontsize=12, fontweight='bold')
ax2.set_xlabel('Year')
ax2.set_ylabel('Growth (%)')
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax2.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bar, ret in zip(bars, returns):
    height = bar.get_height()
    ax2.annotate(f'{ret:.1f}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3 if height >= 0 else -10),
                textcoords="offset points",
                ha='center', va='bottom' if height >= 0 else 'top',
                fontsize=8)

# Plot 3: Volatility Over Time
ax3 = axes[2]
ax3.plot(data['Date'], data['Volatility_20d'] * 100, color='purple', linewidth=0.8, label='20-day Rolling Volatility')
ax3.fill_between(data['Date'], data['Volatility_20d'] * 100, alpha=0.3, color='purple')
ax3.set_title('Stock Volatility Over Time (Annualized)', fontsize=12, fontweight='bold')
ax3.set_xlabel('Date')
ax3.set_ylabel('Volatility (%)')
ax3.grid(True, alpha=0.3)

# Add average volatility line
avg_vol = data['Volatility_20d'].mean() * 100
ax3.axhline(y=avg_vol, color='red', linestyle='--', 
            label=f'Avg Volatility: {avg_vol:.1f}%')
ax3.legend()

plt.tight_layout()
plt.savefig('stock_analysis_visualization.png', dpi=150, bbox_inches='tight')
print("Visualization saved to stock_analysis_visualization.png")

# Create additional detailed visualization
fig2, axes2 = plt.subplots(2, 2, figsize=(14, 10))
fig2.suptitle('LVMH Stock Detailed Analysis', fontsize=16, fontweight='bold')

# Subplot 1: Price history with volume
ax = axes2[0, 0]
ax.plot(data['Date'], data['Close'], color='green', linewidth=1)
ax.set_title('Stock Price History', fontsize=12, fontweight='bold')
ax.set_xlabel('Date')
ax.set_ylabel('Close Price ($)')
ax.grid(True, alpha=0.3)

# Subplot 2: Monthly average volume
monthly_volume = data.groupby(data['Date'].dt.to_period('M'))['Volume'].mean()
ax = axes2[0, 1]
ax.bar(range(len(monthly_volume)), monthly_volume.values, color='blue', alpha=0.6)
ax.set_title('Monthly Average Volume', fontsize=12, fontweight='bold')
ax.set_xlabel('Month')
ax.set_ylabel('Average Volume')
ax.grid(True, alpha=0.3, axis='y')

# Subplot 3: Returns distribution
ax = axes2[1, 0]
returns_clean = data['Returns'].dropna()
ax.hist(returns_clean * 100, bins=50, color='orange', edgecolor='black', alpha=0.7)
ax.axvline(x=returns_clean.mean() * 100, color='red', linestyle='--', 
           label=f'Mean: {returns_clean.mean()*100:.2f}%')
ax.set_title('Daily Returns Distribution', fontsize=12, fontweight='bold')
ax.set_xlabel('Daily Return (%)')
ax.set_ylabel('Frequency')
ax.legend()
ax.grid(True, alpha=0.3)

# Subplot 4: Volatility vs Returns scatter
ax = axes2[1, 1]
scatter_data = data[['Volatility_20d', 'Returns']].dropna()
ax.scatter(scatter_data['Volatility_20d'] * 100, scatter_data['Returns'] * 100, 
           alpha=0.3, color='purple', s=10)
ax.set_title('Volatility vs Returns', fontsize=12, fontweight='bold')
ax.set_xlabel('Volatility (%)')
ax.set_ylabel('Daily Return (%)')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('stock_analysis_detailed.png', dpi=150, bbox_inches='tight')
print("Detailed visualization saved to stock_analysis_detailed.png")

# ============================================================
# Summary Statistics
# ============================================================
print()
print("=" * 60)
print("SUMMARY STATISTICS")
print("=" * 60)

summary = {
    'data_info': {
        'start_date': str(data['Date'].min()),
        'end_date': str(data['Date'].max()),
        'total_trading_days': len(data)
    },
    'price_stats': {
        'min_price': float(data['Close'].min()),
        'max_price': float(data['Close'].max()),
        'mean_price': float(data['Close'].mean()),
        'current_price': float(data['Close'].iloc[-1])
    },
    'volume_stats': {
        'avg_daily_volume': float(data['Volume'].mean()),
        'max_volume': int(data['Volume'].max()),
        'min_volume': int(data['Volume'].min())
    },
    'return_stats': {
        'mean_daily_return': float(data['Returns'].mean()),
        'std_daily_return': float(data['Returns'].std()),
        'mean_annual_return': float(growth_stats['average_annual_return']),
        'total_return': float(growth_stats['total_growth'])
    },
    'volatility_stats': {
        'mean_annual_volatility': float(volatility_stats['mean_volatility']),
        'max_annual_volatility': float(volatility_stats['max_volatility']),
        'min_annual_volatility': float(volatility_stats['min_volatility'])
    }
}

joblib.dump(summary, 'summary_stats.pkl')
print("\nSummary statistics saved to summary_stats.pkl")

print(f"\nPrice Range: ${summary['price_stats']['min_price']:.2f} - ${summary['price_stats']['max_price']:.2f}")
print(f"Current Price: ${summary['price_stats']['current_price']:.2f}")
print(f"Mean Daily Volume: {summary['volume_stats']['avg_daily_volume']:,.0f}")
print(f"Mean Annual Return: {summary['return_stats']['mean_annual_return']:.2%}")
print(f"Mean Annual Volatility: {summary['volatility_stats']['mean_annual_volatility']:.2%}")

print()
print("=" * 60)
print("ANALYSIS COMPLETE!")
print("=" * 60)
print("\nGenerated files:")
print("  - volatility_analysis.pkl")
print("  - growth_analysis.pkl") 
print("  - summary_stats.pkl")
print("  - stock_analysis_visualization.png")
print("  - stock_analysis_detailed.png")

plt.show()

