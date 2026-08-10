"""Train a volume prediction model using a time-based train/test split.
Saves volume_model.pkl and volume_scaler.pkl. Evaluates a naive baseline (train mean)
and prints MSE/R2 for both model and baseline. Optionally performs a simple
walk-forward evaluation.
"""
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score


def main(
    data_path="Data/LV.csv",
    model_path="volume_model.pkl",
    scaler_path="volume_scaler.pkl",
    test_fraction=0.2,
    n_estimators=100,
):
    data = pd.read_csv(data_path)
    y = data["Volume"].values
    X = data[["Open", "High", "Low", "Close"]].values

    scaler = StandardScaler()
    Xn = scaler.fit_transform(X)

    n = len(Xn)
    split = int(n * (1 - test_fraction))
    X_train, X_test = Xn[:split], Xn[split:]
    y_train, y_test = y[:split], y[split:]

    model = RandomForestRegressor(n_estimators=n_estimators, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"Model MSE: {mse:.4f}, R2: {r2:.4f}")

    # naive baseline: train mean
    import numpy as _np

    naive_pred = _np.full_like(y_test, _np.mean(y_train), dtype=float)
    mse_naive = mean_squared_error(y_test, naive_pred)
    r2_naive = r2_score(y_test, naive_pred)
    print(f"Naive baseline (train mean) MSE: {mse_naive:.4f}, R2: {r2_naive:.4f}")

    # simple walk-forward evaluation (expanding window)
    # start with 50% of data as initial training
    init = max(2, int(len(Xn) * 0.5))
    preds = []
    trues = []
    from sklearn.ensemble import RandomForestRegressor as _RFR
    for i in range(init, n):
        Xi_train = Xn[:i]
        yi_train = y[:i]
        Xi_test = Xn[i : i + 1]
        yi_test = y[i : i + 1]
        m = _RFR(n_estimators=50, random_state=42)
        m.fit(Xi_train, yi_train)
        p = m.predict(Xi_test)
        preds.append(p[0])
        trues.append(yi_test[0])
    if preds:
        mse_wf = mean_squared_error(trues, preds)
        r2_wf = r2_score(trues, preds)
        print(f"Walk-forward MSE: {mse_wf:.4f}, R2: {r2_wf:.4f}")

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    print(f"Saved model to {model_path} and scaler to {scaler_path}")


if __name__ == "__main__":
    main()
