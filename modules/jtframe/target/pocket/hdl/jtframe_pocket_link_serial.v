/*  This file is part of JTFRAME.
    JTFRAME program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    JTFRAME program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with JTFRAME.  If not, see <http://www.gnu.org/licenses/>.

    Author: Borja Burgos
    Date: 30-8-2026 */

`timescale 1ns/1ps

/*  JTFRAME Pocket Link2P fixed-slot serial endpoint.

    The Host generates SCK. The Join oversamples the asynchronous cable SCK
    in clk and changes SO only after a synchronized falling edge. A low SCK
    inter-slot gap lets a Join that attached mid-slot recover packet framing.

    Packet fields are opaque here; only the trailing CRC is checked.
    CRC_BITS selects legacy CRC-8/0x07 or CRC-32/MPEG-2 for Link2P v2.
*/

module jtframe_pocket_link_serial #(
    parameter HOST        = 1,
    parameter PACKET_BITS = 192,
    parameter CRC_BITS    = 8,
    parameter HALF_DIV    = 96,
    parameter GAP_CYCLES  = 768,
    parameter GAP_DETECT  = 384
)(
    input                        clk,
    input                        rst,
    input      [PACKET_BITS-1:0] tx_packet,
    output reg [PACKET_BITS-1:0] rx_packet,
    output reg                   rx_valid,
    output reg                   rx_crc_ok,
    input                        serial_in,
    input                        sck_in,
    output reg                   serial_out,
    output reg                   sck_out,
    output                       sck_oe,
    output reg                   slot_active
);

assign sck_oe = HOST != 0;

reg [PACKET_BITS-1:0] tx_shift;
reg [PACKET_BITS-1:0] rx_shift;
reg [15:0]            bit_count;
localparam [CRC_BITS-1:0] CRC_POLY = CRC_BITS == 32 ? 32'h04c1_1db7 : 32'h07;
localparam [CRC_BITS-1:0] CRC_INIT = CRC_BITS == 32 ? 32'hffff_ffff : 32'd0;
reg [CRC_BITS-1:0] rx_crc_calc;

function [CRC_BITS-1:0] crc_next;
    input [CRC_BITS-1:0] crc_in;
    input       data_bit;
    reg         feedback;
    reg [CRC_BITS-1:0]   crc;
    begin
        feedback = crc_in[CRC_BITS-1] ^ data_bit;
        crc = {crc_in[CRC_BITS-2:0], 1'b0};
        if (feedback) crc = crc ^ CRC_POLY;
        crc_next = crc;
    end
endfunction

generate
if (HOST != 0) begin : g_host
    (* altera_attribute = {"-name SYNCHRONIZER_IDENTIFICATION FORCED_IF_ASYNCHRONOUS"} *) reg [2:0] si_sync;
    reg [15:0] divider;
    reg [31:0] gap_count;
    reg        finishing;

    always @(posedge clk) begin
        si_sync  <= {si_sync[1:0], serial_in};
        rx_valid <= 1'b0;
        rx_crc_ok <= 1'b0;

        if (rst) begin
            si_sync      <= 3'b111;
            tx_shift    <= {PACKET_BITS{1'b1}};
            rx_shift    <= {PACKET_BITS{1'b0}};
            rx_packet   <= {PACKET_BITS{1'b0}};
            rx_crc_calc <= CRC_INIT;
            serial_out  <= 1'b1;
            sck_out     <= 1'b0;
            slot_active <= 1'b0;
            bit_count   <= 16'd0;
            divider     <= 16'd0;
            gap_count   <= 32'd0;
            finishing   <= 1'b0;
        end else if (!slot_active) begin
            sck_out    <= 1'b0;
            divider    <= 16'd0;
            finishing  <= 1'b0;
            serial_out <= tx_packet[PACKET_BITS-1];

            if (gap_count == GAP_CYCLES-1) begin
                tx_shift    <= tx_packet;
                rx_shift    <= {PACKET_BITS{1'b0}};
                rx_crc_calc <= CRC_INIT;
                serial_out  <= tx_packet[PACKET_BITS-1];
                bit_count   <= 16'd0;
                gap_count   <= 32'd0;
                slot_active <= 1'b1;
            end else begin
                gap_count <= gap_count + 1'd1;
            end
        end else if (divider == HALF_DIV-1) begin
            divider <= 16'd0;

            if (!sck_out) begin
                // Rising cable edge: both peers sample SI.
                sck_out  <= 1'b1;
                rx_shift <= {rx_shift[PACKET_BITS-2:0], si_sync[2]};
                if (bit_count < PACKET_BITS-CRC_BITS)
                    rx_crc_calc <= crc_next(rx_crc_calc, si_sync[2]);
                if (bit_count == PACKET_BITS-1) begin
                    rx_packet <= {rx_shift[PACKET_BITS-2:0], si_sync[2]};
                    rx_valid  <= 1'b1;
                    rx_crc_ok <= rx_crc_calc == {rx_shift[CRC_BITS-2:0], si_sync[2]};
                    finishing <= 1'b1;
                end
            end else begin
                // Falling cable edge: prepare SO for the next rising edge.
                sck_out <= 1'b0;
                if (finishing) begin
                    serial_out  <= tx_packet[PACKET_BITS-1];
                    slot_active <= 1'b0;
                    gap_count   <= 32'd0;
                    finishing   <= 1'b0;
                end else begin
                    tx_shift   <= {tx_shift[PACKET_BITS-2:0], 1'b1};
                    serial_out <= tx_shift[PACKET_BITS-2];
                    bit_count  <= bit_count + 1'd1;
                end
            end
        end else begin
            divider <= divider + 1'd1;
        end
    end
end else begin : g_join
    (* altera_attribute = {"-name SYNCHRONIZER_IDENTIFICATION FORCED_IF_ASYNCHRONOUS"} *) reg [2:0] sck_sync;
    (* altera_attribute = {"-name SYNCHRONIZER_IDENTIFICATION FORCED_IF_ASYNCHRONOUS"} *) reg [2:0] si_sync;
    reg [31:0] edge_idle;

    wire sck_rise = sck_sync[2:1] == 2'b01;
    wire sck_fall = sck_sync[2:1] == 2'b10;

    always @(posedge clk) begin
        sck_sync <= {sck_sync[1:0], sck_in};
        si_sync  <= {si_sync[1:0], serial_in};
        rx_valid <= 1'b0;
        rx_crc_ok <= 1'b0;
        sck_out  <= 1'b0;

        if (rst) begin
            sck_sync    <= 3'b000;
            si_sync     <= 3'b111;
            tx_shift    <= {PACKET_BITS{1'b1}};
            rx_shift    <= {PACKET_BITS{1'b0}};
            rx_packet   <= {PACKET_BITS{1'b0}};
            rx_crc_calc <= CRC_INIT;
            serial_out  <= 1'b1;
            slot_active <= 1'b0;
            bit_count   <= 16'd0;
            edge_idle   <= 32'd0;
        end else begin
            if (sck_rise || sck_fall) begin
                edge_idle <= 32'd0;
            end else if (edge_idle != 32'hffff_ffff) begin
                edge_idle <= edge_idle + 1'd1;
            end

            // The deliberately long low gap is the packet delimiter.
            if (!sck_sync[2] && edge_idle >= GAP_DETECT-1) begin
                tx_shift    <= tx_packet;
                serial_out  <= tx_packet[PACKET_BITS-1];
                slot_active <= 1'b0;
                bit_count   <= 16'd0;
                rx_crc_calc <= CRC_INIT;
            end

            if (sck_rise) begin
                if (!slot_active) begin
                    slot_active <= 1'b1;
                    bit_count   <= 16'd0;
                    rx_shift    <= {{(PACKET_BITS-1){1'b0}}, si_sync[2]};
                    rx_crc_calc <= crc_next(CRC_INIT, si_sync[2]);
                end else begin
                    rx_shift <= {rx_shift[PACKET_BITS-2:0], si_sync[2]};
                    if (bit_count < PACKET_BITS-CRC_BITS)
                        rx_crc_calc <= crc_next(rx_crc_calc, si_sync[2]);
                end

                if (slot_active && bit_count == PACKET_BITS-1) begin
                    rx_packet   <= {rx_shift[PACKET_BITS-2:0], si_sync[2]};
                    rx_valid    <= 1'b1;
                    rx_crc_ok   <= rx_crc_calc == {rx_shift[CRC_BITS-2:0], si_sync[2]};
                    slot_active <= 1'b0;
                    tx_shift    <= tx_packet;
                    serial_out  <= tx_packet[PACKET_BITS-1];
                end
            end else if (sck_fall && slot_active) begin
                tx_shift   <= {tx_shift[PACKET_BITS-2:0], 1'b1};
                serial_out <= tx_shift[PACKET_BITS-2];
                bit_count  <= bit_count + 1'd1;
            end
        end
    end
end
endgenerate

endmodule
