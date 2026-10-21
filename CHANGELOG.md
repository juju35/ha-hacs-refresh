# Changelog

## 0.1.0

### What's new
- First release: checks every repository downloaded with HACS for updates on the server, four at a time, then refreshes HACS' update entities.
- **Check for updates** button and `hacs_refresh.check_updates` action (administrators only), with an optional `wait`.
- Automatic check at the interval set in the integration options (24 hours by default, `0` to turn it off).
- **Status** sensor with the progress, the number of updates found and the repositories that failed, and a **Last check** sensor.
- English and French.
