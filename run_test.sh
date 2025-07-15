#!/bin/bash
# Test Runner Script
# Starts the main application in the background and then runs tests

echo "Starting Widget Automation Tool..."

# Start the main application in the background
start_debug.bat &
APP_PID=$!

# Give the application time to start
echo "Waiting for application to initialize..."
sleep 2

# Run the standalone test
echo "Running standalone test..."
python standalone_test_runner.py overlay_expansion

# Store test result
TEST_RESULT=$?

# Clean up - kill the application
echo "Cleaning up..."
taskkill /F /PID $APP_PID 2>/dev/null

echo "Test completed with result: $TEST_RESULT"
exit $TEST_RESULT
