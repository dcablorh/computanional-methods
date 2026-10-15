// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract RaffleVulnerable {
    address public lastWinner;
    uint256 public pot;

    function enter() external payable {
        pot += msg.value;
    }

    function draw() external {
        if (block.timestamp % 60 == 0) {
            lastWinner = msg.sender;
        }
    }
}
