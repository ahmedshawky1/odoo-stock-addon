#!/bin/bash

# Test script for all stock market routes
BASE_URL="http://158.220.121.173:8443"
ROUTES=(
    "/my"
    "/my/home"
    "/my/portfolio"
    "/my/orders"
    "/my/order/new"
    "/my/market"
    "/my/commissions"
    "/market"
    "/market/home"
    "/market/portfolio"
    "/market/trading"
    "/market/orders"
    "/market/securities"
    "/market/session"
    "/market/reports"
    "/market/ipo"
    "/market/deposits"
    "/market/loans"
    "/market/clients"
)

echo "Testing all stock market routes..."
echo "=================================="

for route in "${ROUTES[@]}"; do
    echo -n "Testing $route: "
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$route")
    echo "HTTP $status_code"
done

echo "=================================="
echo "Test completed."