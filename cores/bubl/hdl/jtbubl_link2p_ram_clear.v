/*  This file is part of JTCORES.
    JTCORES program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    JTCORES program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with JTCORES.  If not, see <http://www.gnu.org/licenses/>.

    Author: Borja Burgos
    Date: 30-8-2026 */

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
