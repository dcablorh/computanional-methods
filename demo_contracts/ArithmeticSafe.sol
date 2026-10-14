// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ArithmeticSafe {
    mapping(address => uint256) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function batchTransfer(address[] memory receivers, uint256 amount) public {
        uint256 totalAmount = receivers.length * amount; // checked overflow in 0.8.0+
        require(balances[msg.sender] >= totalAmount, "Insufficient balance");

        for (uint256 i = 0; i < receivers.length; i++) {
            balances[receivers[i]] += amount;
        }
        balances[msg.sender] -= totalAmount;
    }
}
