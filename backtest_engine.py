import backtrader as bt
import pandas as pd

class TLCITStrategy(bt.Strategy):
    params = dict(entry_score=8.0, exit_score=2.0)

    def __init__(self):
        self.signal = self.datas[0].signal_score
        self.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    def next(self):
        if not self.position and self.signal[0] >= self.p.entry_score:
            size = self.broker.getvalue() * 0.1 / self.data.close[0]
            self.buy(size=size)
        elif self.position and self.signal[0] <= self.p.exit_score:
            self.close()

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            dt = self.data.datetime.date()
            print(f"{dt} - Order {order.Status[order.status]}: {order.executed.size} @ {order.executed.price}")

if __name__ == "__main__":
    cerebro = bt.Cerebro(maxcpus=4)
    cerebro.addstrategy(
        TLCITStrategy,
        entry_score=[6, 7, 8, 9],
        exit_score=[2, 3, 4]
    )
    df = pd.read_csv('historical_signals.csv', parse_dates=True, index_col='date')
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.broker.setcommission(commission=0.0005)
    cerebro.broker.set_slippage_perc(perc=0.001)
    cerebro.broker.setcash(100000)
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

    print("Starting Portfolio Value:", cerebro.broker.getvalue())
    results = cerebro.run(maxcpus=4)

    if isinstance(results[0], list):
        flat = [res[0] for res in results]
        best = max(flat, key=lambda x: x.analyzers.sharpe.get_analysis().get('sharperatio', 0))
    else:
        best = results[0]

    strat = best
    print("Final Portfolio Value:", cerebro.broker.getvalue())
    print("Sharpe Ratio:", strat.analyzers.sharpe.get_analysis())
    print("Drawdown:", strat.analyzers.drawdown.get_analysis())
    print("Trades:", strat.analyzers.trades.get_analysis())
