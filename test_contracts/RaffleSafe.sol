// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract RaffleSafe {
    address public lastWinner;
    uint256 public pot;
    uint256 public commitBlock;

    function enter() external payable {
        pot += msg.value;
    }

    function commit() external {
        commitBlock = block.number;
    }

    function draw(bytes32 seed) external {
        require(block.number > commitBlock + 5, "too early");
        if (uint256(keccak256(abi.encode(seed, blockhash(commitBlock)))) % 2 == 0) {
            lastWinner = msg.sender;
        }
    }
}
