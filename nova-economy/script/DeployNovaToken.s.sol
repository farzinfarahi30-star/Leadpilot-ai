// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script} from "forge-std/Script.sol";
import {NovaToken} from "../contracts/NovaToken.sol";

contract DeployNovaToken is Script {
    function run() external returns (NovaToken token) {
        uint256 deployerKey = vm.envUint("NOVA_DEPLOYER_PRIVATE_KEY");
        address owner = vm.envAddress("NOVA_OWNER");
        uint256 cap = vm.envUint("NOVA_MAX_SUPPLY");

        require(owner != address(0), "NOVA_OWNER is zero");
        require(cap > 0, "NOVA_MAX_SUPPLY is zero");

        vm.startBroadcast(deployerKey);
        token = new NovaToken(owner, cap);
        vm.stopBroadcast();
    }
}
