// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract LedgerSafe {
    mapping(address => uint256) public balanceOf;

    function mint(uint256 amount) public {
        balanceOf[msg.sender] += amount;
    }

    function move(address to, uint256 amount) public {
        require(balanceOf[msg.sender] >= amount, "insufficient balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
    }
}
