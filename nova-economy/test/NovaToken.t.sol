// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {NovaToken} from "../contracts/NovaToken.sol";

contract NovaTokenTest is Test {
    NovaToken token;
    address owner = address(0x1);
    address user = address(0x2);

    function setUp() public {
        token = new NovaToken(owner, 1_000_000 ether);
    }

    function testCap() public {
        vm.prank(owner);
        token.mint(user, 1_000_000 ether);
        assertEq(token.totalSupply(), 1_000_000 ether);
        vm.expectRevert("cap exceeded");
        vm.prank(owner);
        token.mint(user, 1);
    }

    function testPause() public {
        vm.prank(owner);
        token.mint(user, 10 ether);
        vm.prank(owner);
        token.pause();
        vm.expectRevert();
        vm.prank(user);
        token.transfer(owner, 1 ether);
    }
}
