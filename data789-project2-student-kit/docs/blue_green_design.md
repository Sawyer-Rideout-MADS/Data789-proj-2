# Blue-Green Deployment Design (fill this in)

> Deliverable for Part B. Explain the strategy and show it working with the
> provided `docker-compose.blue-green.yml` + `switch_traffic.sh`. No Kubernetes.

## 1. Strategy
- What "blue" and "green" are here, and which one serves live traffic.
- How a new version is brought up alongside the old one.

Blue represents one version of the API and is available on port `8001`.
Green represents the other version of the API and is available on port `8002`.
nginx provides the stable public endpoint on port `8080`.

Only one version receives live traffic through nginx at a time. The other version remains running as the inactive environment. This allows a new version to be built, started, and tested while the current version continues serving requests.

In this project, both `api-blue` and `api-green` are started through `deployment/docker-compose.blue-green.yml`. The inactive version can be checked before traffic is switched to it, which reduces the risk of routing requests to a version that failed to start correctly.


## 2. Cutover
- How `switch_traffic.sh` flips nginx from one version to the other.
- Why the reload is zero-downtime (in-flight requests drain).

The `deployment/switch_traffic.sh` script determines which API version is currently active and updates the nginx configuration to point to the inactive version.

For example, if blue is currently serving traffic, the script updates the nginx upstream so that new requests are sent to green instead. After updating the configuration, the script reloads nginx.

The stable client endpoint remains http://localhost:8080

Clients do not need to change URLs during deployment because nginx always provides the same endpoint.

Reloading nginx supports a zero-downtime deployment because nginx reloads its configuration without completely stopping the service. Existing worker processes continue handling requests that are already in progress, while new worker processes begin routing requests to the updated API version. This allows in-flight requests to complete without interruption while new requests are directed to the newly active version.


## 3. Health gate & rollback
- The health check performed before cutover.
- How you roll back (hint: run the switch again).

Before switching traffic, `switch_traffic.sh` checks the `/health` endpoint of the inactive API version. The deployment only proceeds if the inactive version returns a successful health response.

This health check prevents nginx from routing requests to an API instance that has failed to start or is otherwise unavailable.

Rollback uses the same script. Because both blue and green remain running throughout the deployment, the previous version is still available after the switch. Running the script again changes nginx back to the previous version.

For example:

Blue active  →  Run switch script  →  Green active

Green active →  Run switch script  →  Blue active

Since the previous version never stops running, rollback is nearly instantaneous and does not require rebuilding or restarting the application.


## 4. How this maps to Kubernetes (1 short paragraph)
- What the nginx upstream + reload becomes in K8s (Service selector / two
  Deployments). You will build the K8s version in a later unit.

In Kubernetes, the blue and green environments would typically be implemented as two separate Deployments. Instead of nginx managing traffic, a Kubernetes Service would provide the stable endpoint. Traffic would be switched by changing the Service selector from the blue Deployment labels to the green Deployment labels. Kubernetes readiness probes would perform the same role as the `/health` endpoint by ensuring traffic is only routed to healthy pods. If the new version failed after deployment, the Service selector could simply be switched back to the previous Deployment.


## 5. Evidence
- Screenshot / terminal capture of a switch with no dropped requests.

included in other files under docs
