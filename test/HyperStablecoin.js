const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("HyperStablecoin", function () {
  it("Should mint with valid signature", async function () {
    const [owner, oracle] = await ethers.getSigners();
    const Contract = await ethers.getContractFactory("HyperStablecoin");
    const contract = await Contract.deploy(oracle.address);
    await contract.deployed();
    
    const amount = ethers.utils.parseEther("100");
    const message = ethers.utils.keccak256(ethers.utils.defaultAbiCoder.encode(["string", "address", "uint256"], ["mint", owner.address, amount]));
    const signature = await oracle.signMessage(ethers.utils.arrayify(message));
    
    await contract.mint(owner.address, amount, signature);
    expect(await contract.balanceOf(owner.address)).to.equal(amount);
  });
});
