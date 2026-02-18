# Healthchecks.io → PagerDuty Integration

## Setup Steps

1. **Sign up** at https://healthchecks.io/ (free tier: 20 checks)

2. **Add PagerDuty Integration:**
   - Go to: Integrations → Add Integration → PagerDuty
   - Click "Add Integration" next to PagerDuty
   - Authorize with PagerDuty (OAuth)
   - Select service to send alerts to

3. **Create a Check:**
   - Go to: Checks → Add Check
   - Set name, schedule (e.g., every 5 minutes)
   - Copy the ping URL

4. **Ping from your service:**
   ```bash
   # Success ping
   curl -fsS --retry 3 https://hc-ping.com/your-uuid-here
   
   # Start ping (for long jobs)
   curl -fsS --retry 3 https://hc-ping.com/your-uuid-here/start
   
   # Fail ping
   curl -fsS --retry 3 https://hc-ping.com/your-uuid-here/fail
   ```

5. **Cron example:**
   ```bash
   # Add to crontab
   */5 * * * * /path/to/job.sh && curl -fsS https://hc-ping.com/your-uuid
   ```

## Use Cases
- Cron job monitoring
- Backup verification
- Scheduled task heartbeats
- Dead man's switch alerts
