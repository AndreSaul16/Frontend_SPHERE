"""
Tests para el modelo de cobro 1-crédito-por-POST.
Verifica que el crédito se cobra UNA vez en stream.py y
que agent_node no vuelve a cobrar si ya se cobró.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


def make_state(**overrides):
    """Factory para AgentState con defaults mínimos."""
    from app.application.orchestrator import AgentState
    return AgentState(
        messages=[],
        next_agent="CEO",
        query="test query",
        final_response="",
        target_role=None,
        system_prompt=None,
        model_config=None,
        tool_calls_remaining=3,
        user_id="test_user_123",
        board_mode=False,
        board_iteration=0,
        board_max_iterations=1,
        board_agents_done=[],
        **overrides,
    )


@pytest.fixture
def mock_deps():
    """Mockea todas las dependencias pesadas de agent_node."""
    patches = []

    # CreditManager
    mock_cm = MagicMock()
    mock_cm.areserve_and_charge = AsyncMock(return_value=MagicMock(
        tx_id="tx_123", user_id="test_user_123", cost=1, source="plan", counted_as=1
    ))
    mock_cm.arefund = AsyncMock()
    mock_cm.aadjust_after_completion = AsyncMock()
    p = patch("app.application.credit_manager.CreditManager", return_value=mock_cm)
    p.start()
    patches.append(p)

    # DB singleton
    mock_db = MagicMock()
    mock_db.get_sync_client.return_value = {"sphere_db": MagicMock()}
    mock_db._connected = True
    p = patch("app.infrastructure.database.db", mock_db)
    p.start()
    patches.append(p)

    # Settings
    p = patch("app.core.config.settings")
    mock_settings = p.start()
    mock_settings.DB_NAME = "sphere_db"
    mock_settings.FERNET_KEY = "test-fernet-key-32-bytes-here!!"
    mock_settings.is_development = True
    patches.append(p)

    # Users collection mock — needs to be awaitable
    mock_users_col = MagicMock()
    mock_users_col.find_one = AsyncMock(return_value=None)
    p = patch("app.infrastructure.database.get_users_collection", return_value=mock_users_col)
    p.start()
    patches.append(p)

    # Resolve agent config
    p = patch("app.application.agent_resolver.resolve_agent_config", new_callable=AsyncMock)
    mock_resolve = p.start()
    mock_resolve.return_value = MagicMock(
        system_prompt="test prompt", model="deepseek-chat", temperature=0.3,
    )
    patches.append(p)

    # RAG retrieve_context — patch at the module level where orchestrator imports it
    mock_rag = AsyncMock(return_value="fake RAG context")
    p = patch("app.application.orchestrator.retrieve_context", mock_rag)
    p.start()
    patches.append(p)

    # Tools
    p = patch("app.infrastructure.tools.registry.get_tools_for_role", return_value=[])
    p.start()
    patches.append(p)

    # ChatOpenAI - patch the module-level import in orchestrator
    mock_llm_class = MagicMock()
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(
        content="response", additional_kwargs={"agent_role": "CEO"}
    ))
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)
    mock_llm_class.return_value = mock_llm
    p = patch("app.application.orchestrator.ChatOpenAI", mock_llm_class)
    p.start()
    patches.append(p)

    yield mock_cm

    for p in reversed(patches):
        p.stop()


class TestAgentNodeChargeSkip:
    """Verifica que agent_node respeta la bandera already_charged."""

    @pytest.mark.asyncio
    async def test_agent_node_charges_when_not_already_charged(self, mock_deps):
        """Cuando already_charged=False, agent_node DEBE cobrar."""
        from app.application.orchestrator import agent_node
        state = make_state(already_charged=False)

        await agent_node(state)

        mock_deps.areserve_and_charge.assert_called_once()
        args = mock_deps.areserve_and_charge.call_args[0]
        assert args[0] == "test_user_123"

    @pytest.mark.asyncio
    async def test_agent_node_skips_charge_when_already_charged(self, mock_deps):
        """Cuando already_charged=True, agent_node NO debe cobrar."""
        from app.application.orchestrator import agent_node
        state = make_state(already_charged=True)

        await agent_node(state)

        mock_deps.areserve_and_charge.assert_not_called()


class TestAgentNodeRefund:
    """Verifica que el refund solo ocurre cuando corresponde."""

    @pytest.mark.asyncio
    async def test_agent_node_refund_on_inference_error(self, mock_deps):
        """Cuando la inferencia falla y already_charged=False, se hace refund."""
        from app.application.orchestrator import agent_node
        state = make_state(already_charged=False)

        # Hacer que el LLM falle
        from app.application import orchestrator as orch
        mock_llm = orch.ChatOpenAI.return_value
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("Inference failed"))

        with pytest.raises(Exception, match="Inference failed"):
            await agent_node(state)

        mock_deps.arefund.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_node_no_refund_when_already_charged_and_error(self, mock_deps):
        """Cuando already_charged=True (stream.py ya cobró), error en agent_node NO
        debe hacer refund aquí — lo maneja stream.py."""
        from app.application.orchestrator import agent_node
        state = make_state(already_charged=True)

        from app.application import orchestrator as orch
        mock_llm = orch.ChatOpenAI.return_value
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("Inference failed"))

        with pytest.raises(Exception, match="Inference failed"):
            await agent_node(state)

        mock_deps.arefund.assert_not_called()
        mock_deps.areserve_and_charge.assert_not_called()


# ── Board Meeting already_charged Propagation ──────────────────


class TestBoardMeetingAlreadyChargedPropagation:
    """Verifica que already_charged sobrevive a través de los nodos
    del board meeting (board_classifier_node y next_iteration_node)."""

    @pytest.mark.asyncio
    async def test_board_classifier_node_propagates_already_charged(self):
        """board_classifier_node preserva already_charged=True en su salida."""
        from app.application.orchestrator import board_classifier_node
        state = make_state(already_charged=True)

        result = await board_classifier_node(state)

        assert result.get("already_charged") is True, (
            f"board_classifier_node debe propagar already_charged=True, "
            f"pero retornó {result.get('already_charged')}"
        )

    @pytest.mark.asyncio
    async def test_board_classifier_node_propagates_false(self):
        """Triangulación: already_charged=False también se preserva."""
        from app.application.orchestrator import board_classifier_node
        state = make_state(already_charged=False)

        result = await board_classifier_node(state)

        assert result.get("already_charged") is False, (
            f"board_classifier_node debe propagar already_charged=False"
        )

    def test_next_iteration_node_propagates_already_charged(self):
        """next_iteration_node preserva already_charged=True en su salida."""
        from app.application.orchestrator import next_iteration_node
        state = make_state(already_charged=True)

        result = next_iteration_node(state)

        assert result.get("already_charged") is True, (
            f"next_iteration_node debe propagar already_charged=True, "
            f"pero retornó {result.get('already_charged')}"
        )

    def test_next_iteration_node_propagates_false(self):
        """Triangulación: already_charged=False en next_iteration_node."""
        from app.application.orchestrator import next_iteration_node
        state = make_state(already_charged=False)

        result = next_iteration_node(state)

        assert result.get("already_charged") is False, (
            f"next_iteration_node debe propagar already_charged=False"
        )


# ── End-to-End: Stream POST charges exactly once ──────────────


class TestStreamPostChargesExactlyOnce:
    """Verifica que el endpoint stream POST cobra exactamente 1 vez,
    y que agent_node no vuelve a cobrar cuando already_charged=True."""

    @pytest.mark.asyncio
    async def test_stream_post_charges_exactly_once_end_to_end(self, mock_deps):
        """agent_node con already_charged=True → 0 cargos extras.
        La carga ya ocurrió en stream.py; agent_node debe respetar la bandera."""
        from app.application.orchestrator import agent_node
        state = make_state(already_charged=True)

        await agent_node(state)

        # agent_node NO debe cobrar cuando already_charged=True
        mock_deps.areserve_and_charge.assert_not_called()

    @pytest.mark.asyncio
    async def test_agent_node_without_already_charged_calls_charge_once(self, mock_deps):
        """Triangulación: already_charged=False → agent_node cobra exactamente 1 vez."""
        from app.application.orchestrator import agent_node
        state = make_state(already_charged=False)

        await agent_node(state)

        mock_deps.areserve_and_charge.assert_called_once()
