import sys

import pytest
import requests

import main


def run_cli(monkeypatch, tmp_path, argv, place):
    monkeypatch.chdir(tmp_path)          # bot.log is written to the working directory
    monkeypatch.setenv("BINANCE_KEY", "k")
    monkeypatch.setenv("BINANCE_SECRET", "s")
    monkeypatch.setattr(main, "place", place)
    monkeypatch.setattr(sys, "argv", ["bot", *argv])
    main.main()


def test_limit_order_is_placed_and_printed(monkeypatch, tmp_path, capsys):
    seen = []

    def place(c, *a):
        seen.append(a)
        return {"orderId": 9, "status": "NEW", "side": "SELL"}

    run_cli(monkeypatch, tmp_path,
            ["--symbol", "btcusdt", "--side", "SELL", "--type", "LIMIT", "--qty", "0.001", "--price", "99000"], place)
    assert seen == [("BTCUSDT", "SELL", "LIMIT", 0.001, 99000.0, None)]
    out = capsys.readouterr().out
    assert "Order placed" in out and "orderId" in out


def test_missing_price_exits_without_calling_the_api(monkeypatch, tmp_path):
    def place(*a):
        raise AssertionError("must not be called")

    with pytest.raises(SystemExit) as ei:
        run_cli(monkeypatch, tmp_path, ["--symbol", "BTCUSDT", "--side", "BUY", "--type", "LIMIT", "--qty", "1"], place)
    assert "price is required" in str(ei.value)


def test_api_error_shows_binance_code_and_message(monkeypatch, tmp_path):
    def place(*a):
        e = requests.exceptions.HTTPError()
        e.api_msg = {"code": -2019, "msg": "Margin is insufficient."}
        raise e

    with pytest.raises(SystemExit) as ei:
        run_cli(monkeypatch, tmp_path, ["--symbol", "BTCUSDT", "--side", "BUY", "--type", "MARKET", "--qty", "1"], place)
    assert "[-2019] Margin is insufficient." in str(ei.value)


def test_missing_credentials_exit_with_a_clear_message(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BINANCE_KEY", raising=False)
    monkeypatch.delenv("BINANCE_SECRET", raising=False)
    monkeypatch.setattr(sys, "argv", ["bot", "--symbol", "BTCUSDT", "--side", "BUY", "--type", "MARKET", "--qty", "1"])
    with pytest.raises(SystemExit) as ei:
        main.main()
    assert "credentials missing" in str(ei.value)
