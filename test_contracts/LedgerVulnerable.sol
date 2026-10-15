// SPDX-License-Identifier: MIT
pragma solidity ^0.7.6;

contract LedgerVulnerable {
    mapping(address => uint256) public balanceOf;

    function mint(uint256 amount) public {
        balanceOf[msg.sender] += amount;
    }

    function move(address to, uint256 amount) public {
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
    }
}
