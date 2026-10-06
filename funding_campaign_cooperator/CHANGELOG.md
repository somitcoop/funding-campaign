# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- [FIX] Suscripciones: `create()` pasa a `@api.model_create_multi` — el override anterior recibía un único dict y rompía con `load()`, importaciones y creaciones en lote (`AttributeError: 'list' object has no attribute 'get'`)
- [FIX] Se elimina `cooperator_subscription_request_filter_extension.xml`: no estaba en el manifest y duplicaba los filtros de firma de `subscription_request.xml` (además de arrastrar el filtro `partial` inexistente)
- [FIX] Suscripciones: se retira el filtro *Partially Signed* de la búsqueda — `signature_state` solo admite `pending`/`signed`, así que el dominio `'partial'` no devolvía nunca resultados
- [IMP] Suscripciones: nuevo booleano *Contribution Created* (`has_contribution`) en la ficha y en la lista, visible por defecto y filtrable, para saber de un vistazo qué suscripciones ya generaron su aportación
- [IMP] Ficha de la campaña: el smartbutton *Contributions* queda oculto (`invisible="1"`); el código se mantiene por si se recupera
- [IMP] Lista de suscripciones: la columna *Remunerated* se muestra por defecto (`optional="show"`) y el usuario puede ocultarla desde el selector de columnas
- [IMP] Enlace visible con la aportación: la ficha de la suscripción muestra el enlace a la aportación creada (solo si existe) y la lista añade una columna opcional con ella

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
