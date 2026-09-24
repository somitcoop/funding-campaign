# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- [IMP] Cancelling a contribution now cancels its linked `subscription.request`
  (`paid` to `cancelled`); `cancel_subscription_request` also accepts requests
  in the `paid` state

- [IMP] `subscription.request`: new `remunerated` field replacing the legacy
  `increase_remunerated` type (normalized in `create` and in the REST API);
  digital signature and campaign emails now rely on `remunerated`
- [IMP] Deterministic contribution creation from the subscription request:
  the contribution type is resolved from the share product
  (`contribution_type_cash_id` / `contribution_type_wallet_id`) according to
  the remuneration mode, without silent fallback
- [IMP] Migration `17.0.1.1.0`: `increase_remunerated` becomes `increase`
  plus `remunerated = True`
