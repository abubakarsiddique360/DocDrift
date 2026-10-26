# Runtime incident policy

## Purpose

This policy explains how the platform team responds to incidents. It applies to
all production services and to anyone who is on call. Reviewers approve changes in
the operations repository.

## Escalation

Escalate to the engineering manager after thirty minutes without a mitigation.
Escalate to the incident commander channel if two teams are affected.

## Severity levels

Sev 1 means customer-facing outage. Sev 2 means degraded service with a workaround.
Sev 3 means internal impact only.

## On-call rotation

The rotation runs weekly and changes on Monday at 09:00. Handover happens in the
operations channel with a written summary and a list of open risks.

## Cost controls

Every incident review must state the estimated cost of the outage and whether the
mitigation increased infrastructure spend.
