// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract VaultVulnerable {
    mapping(address => uint256) private shares;

    function credit() external payable {
        shares[msg.sender] += msg.value;
    }

    function redeem() external {
        uint256 amount = shares[msg.sender];
        require(amount > 0, "nothing to redeem");
        (bool ok, ) = payable(msg.sender).call{value: amount}("");
        require(ok, "transfer failed");
        shares[msg.sender] = 0;
    }
}
