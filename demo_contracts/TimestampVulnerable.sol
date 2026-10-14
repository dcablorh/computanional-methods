// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TimestampVulnerable {
    uint256 public lastDraw;
    address public winner;

    function play() public {
        require(block.timestamp % 15 == 0, "Not the lucky second");
        winner = msg.sender;
    }
}
