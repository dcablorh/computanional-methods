// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TimestampSafe {
    uint256 public drawBlock;
    address public winner;

    function play(uint256 userGuess) public {
        require(userGuess == 42, "Wrong guess");
        winner = msg.sender;
    }
}
