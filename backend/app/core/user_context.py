"""
Builder del bloque USER_CONTEXT que se inyecta en system prompts.
Convierte el perfil del usuario en un bloque de texto que los agentes
usan para adaptar tono, idioma, moneda y contexto profesional.
"""


def build_user_context_block(user: dict) -> str:
    """
    Construye el bloque USER_CONTEXT a partir del documento User.
    Solo incluye campos poblados (no None/empty).
    """
    lines = []

    display_name = user.get("display_name")
    if display_name:
        lines.append(f"- Nombre: {display_name}")

    # Professional profile
    prof = user.get("professional_profile", {})
    if prof:
        role = prof.get("role")
        if role:
            lines.append(f"- Rol: {role}")

        company = prof.get("company_name")
        industry = prof.get("industry")
        stage = prof.get("company_stage")
        team_size = prof.get("team_size")

        company_parts = []
        if company:
            company_parts.append(company)
        if industry:
            company_parts.append(industry)
        if stage:
            company_parts.append(stage)
        if team_size:
            company_parts.append(f"equipo de {team_size}")

        if company_parts:
            lines.append(f"- Empresa: {', '.join(company_parts)}")

    # Communication style
    comm = user.get("communication_style", {})
    if comm:
        tone = comm.get("tone", "casual")
        verbosity = comm.get("verbosity", "concise")
        register = comm.get("language_register")

        style_parts = [tone, verbosity]
        if register:
            style_parts.append(register)
        lines.append(f"- Estilo preferido: {', '.join(style_parts)}")

    # Locale
    ui = user.get("ui_preferences", {})
    locale = ui.get("locale", "es-ES") if ui else "es-ES"
    lines.append(f"- Idioma: {locale}")

    # Financial preferences
    fin = user.get("financial_preferences", {})
    if fin:
        currency = fin.get("base_currency", "EUR")
        lines.append(f"- Moneda base: {currency}")

    # Nivel de confirmación para acciones destructivas
    if ui:
        confirm_level = ui.get("tool_confirmation_level", "destructive_only")
        if confirm_level == "always":
            lines.append(
                "- Confirmación: SIEMPRE pregunta al usuario antes de ejecutar "
                "cualquier herramienta que escriba o envíe datos."
            )
        elif confirm_level == "destructive_only":
            lines.append(
                "- Confirmación: pregunta explícitamente antes de ejecutar acciones "
                "destructivas (publicar, enviar mensajes, eliminar, invitar)."
            )
        elif confirm_level == "never":
            lines.append(
                "- Confirmación: el usuario permite ejecutar tools sin preguntar."
            )

    if not lines:
        return ""

    return "USER_CONTEXT:\n" + "\n".join(lines)
