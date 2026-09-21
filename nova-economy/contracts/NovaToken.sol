// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ERC20Pausable} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

contract NovaToken is ERC20, ERC20Pausable, Ownable {
    uint256 public immutable maxSupply;

    constructor(address initialOwner, uint256 cap)
        ERC20("Nova", "NOVA")
        Ownable(initialOwner)
    {
        require(initialOwner != address(0), "owner is zero");
        require(cap > 0, "cap is zero");
        maxSupply = cap;
    }

    function mint(address to, uint256 amount) external onlyOwner {
        require(to != address(0), "recipient is zero");
        require(totalSupply() + amount <= maxSupply, "cap exceeded");
        _mint(to, amount);
    }

    function pause() external onlyOwner { _pause(); }
    function unpause() external onlyOwner { _unpause(); }

    function _update(address from, address to, uint256 value)
        internal
        override(ERC20, ERC20Pausable)
    {
        super._update(from, to, value);
    }
}
