// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script} from "forge-std/Script.sol";

interface IERC20Mintable {
    function owner() external view returns (address);
    function maxSupply() external view returns (uint256);
    function totalSupply() external view returns (uint256);
    function mint(address to, uint256 amount) external;
    function approve(address spender, uint256 amount) external returns (bool);
}

interface IRouterV2 {
    function factory() external pure returns (address);
    function WETH() external pure returns (address);
    function addLiquidityETH(address token,uint amountTokenDesired,uint amountTokenMin,uint amountETHMin,address to,uint deadline)
        external payable returns (uint amountToken,uint amountETH,uint liquidity);
}

interface IFactoryV2 {
    function getPair(address tokenA,address tokenB) external view returns (address);
}

contract AddUniswapV2Liquidity is Script {
    address constant ROUTER=0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    function run() external returns(address pair,uint amountToken,uint amountETH,uint liquidity) {
        uint key=vm.envUint("NOVA_OWNER_PRIVATE_KEY");
        address owner=vm.envAddress("NOVA_OWNER");
        address token=vm.envAddress("NOVA_MAINNET_TOKEN");
        uint tokenAmount=vm.envUint("NOVA_MAINNET_LIQUIDITY_TOKENS")*1 ether;
        uint ethAmount=vm.envUint("NOVA_MAINNET_LIQUIDITY_ETH_WEI");
        require(vm.addr(key)==owner,"owner key/address mismatch");
        IERC20Mintable nova=IERC20Mintable(token);
        require(nova.owner()==owner,"token owner mismatch");
        IRouterV2 router=IRouterV2(ROUTER);
        address weth=router.WETH();
        pair=IFactoryV2(router.factory()).getPair(token,weth);
        require(pair==address(0),"Uniswap V2 pair already exists");
        require(tokenAmount>0 && ethAmount>0,"liquidity amounts must be positive");
        require(nova.totalSupply()+tokenAmount<=nova.maxSupply(),"cap exceeded");
        vm.startBroadcast(key);
        nova.mint(owner,tokenAmount);
        require(nova.approve(ROUTER,tokenAmount),"approve failed");
        (amountToken,amountETH,liquidity)=router.addLiquidityETH{value:ethAmount}(
            token,tokenAmount,tokenAmount,ethAmount,owner,block.timestamp+1800
        );
        vm.stopBroadcast();
        require(amountToken==tokenAmount && amountETH==ethAmount && liquidity>0,"liquidity mismatch");
    }
}
