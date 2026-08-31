`timescale 1ns/1ps

/*  Link2P restart RAM scrubber.

    A normal JTBUBL reset reproduces the arcade board's CPU reset and leaves
    external work RAM intact. Reloading an openFPGA core, however, starts its
    inferred RAMs from their initialized contents. Link2P cable recovery needs
    the latter behavior so a discarded game always returns to a clean boot.
*/

module jtbubl_link2p_ram_clear #(
    parameter AW = 13
)(
    input               rst,
    input               clk,
    output reg [AW-1:0] addr = {AW{1'b0}},
    output              we
);

reg primed = 1'b0;

assign we = rst & primed;

always @(posedge clk) begin
    if( !rst ) begin
        addr   <= {AW{1'b0}};
        primed <= 1'b0;
    end else begin
        primed <= 1'b1;
        if( primed ) addr <= addr + 1'd1;
        else          addr <= {AW{1'b0}};
    end
end

endmodule
