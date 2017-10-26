import random

import pytest

import casper.settings as settings
from simulations.analyzer import Analyzer
from simulations.simulation_runner import SimulationRunner
import simulations.utils as utils


@pytest.mark.parametrize(
    'mode, messages_generated_per_round',
    [
        ('rand', settings.NUM_MESSAGES_PER_ROUND),
        ('rrob', 1),
        ('full', 5),
        ('nofinal', 2),
    ]
)
def test_num_messages(validator_set, mode, messages_generated_per_round):
    msg_gen = utils.message_maker(mode)
    simulation_runner = SimulationRunner(validator_set, msg_gen, 100)
    analyzer = Analyzer(simulation_runner)

    # due to random_initialization
    assert analyzer.num_messages() == len(validator_set)

    for i in range(10):
        simulation_runner.step()
        assert analyzer.num_messages() == len(validator_set) + (i + 1) * messages_generated_per_round


@pytest.mark.parametrize(
    'safe_blocks, expected',
    [
        (['C'], 1),
        (['C', 'F', 'H'], 3),
    ]
)
def test_num_safe_messages(simulation_runner, safe_blocks, expected):
    simulation_runner.safe_blocks = safe_blocks
    analyzer = Analyzer(simulation_runner)

    assert round(analyzer.num_safe_messages(), 2) == expected


@pytest.mark.skip(reason="test with mocks broken")
@pytest.mark.parametrize(
    'num_blocks, num_blocks_at_or_below_safe_tip, safe_tip_number, expected',
    [
        (5, 5, 2, 0.40),
        (2, 2, 0, 0.50),
        (2, 0, -1, 0.0),
        (10, 8, 4, 0.375),
        (20, 10, 9, 0.0),
    ]
)
def test_orphan_rate(
        simulation_runner,
        mock_block,
        num_blocks,
        num_blocks_at_or_below_safe_tip,
        safe_tip_number,
        expected
        ):

    if safe_tip_number != -1:
        safe_blocks = [
            mock_block(sequence_number=i, id=random.random())
            for i in range(safe_tip_number + 1)
        ]
        unsafe_blocks = [
            mock_block(sequence_number=random.sample(range(safe_tip_number + 1), 1)[0], id=random.random())
            for i in range(num_blocks_at_or_below_safe_tip - len(safe_blocks))
        ]
    else:
        safe_blocks, unsafe_blocks = [], []
    num_other_blocks = num_blocks - num_blocks_at_or_below_safe_tip
    other_blocks = [
        mock_block(
            sequence_number=random.sample(
                range(safe_tip_number+1, safe_tip_number + num_other_blocks), 1)[0],
            id=random.random()
        )
        for i in range(num_other_blocks)
    ]

    all_blocks = safe_blocks + unsafe_blocks + other_blocks

    simulation_runner.network.global_view.messages = set(all_blocks)
    simulation_runner.safe_blocks = safe_blocks

    analyzer = Analyzer(simulation_runner)

    assert round(analyzer.orphan_rate(), 3) == expected