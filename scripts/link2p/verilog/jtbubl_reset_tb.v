`timescale 1ns/1ps

module test;

localparam AW = 4;
localparam DEPTH = 1 << AW;

reg clk = 1'b0;
reg rst = 1'b0;
reg [AW-1:0] cpu_addr = {AW{1'b0}};
reg [7:0] cpu_data = 8'd0;
reg cpu_we = 1'b0;
wire [AW-1:0] clear_addr;
wire clear_we;
wire [AW-1:0] ram_addr = clear_we ? clear_addr : cpu_addr;
wire [7:0] ram_data = clear_we ? 8'd0 : cpu_data;
wire ram_we = clear_we | cpu_we;
wire [7:0] ram_q;
integer i;

always #5 clk = ~clk;

jtbubl_link2p_ram_clear #(.AW(AW)) u_clear(
    .rst    ( rst        ),
    .clk    ( clk        ),
    .addr   ( clear_addr ),
    .we     ( clear_we   )
);

jtframe_dual_ram #(.AW(AW)) u_ram(
    .clk0   ( clk        ),
    .data0  ( ram_data   ),
    .addr0  ( ram_addr   ),
    .we0    ( ram_we     ),
    .q0     ( ram_q      ),
    .clk1   ( clk        ),
    .data1  ( 8'd0       ),
    .addr1  ( {AW{1'b0}} ),
    .we1    ( 1'b0       ),
    .q1     (            )
);

task read_zero;
    input [AW-1:0] address;
    begin
        @(negedge clk) cpu_addr = address;
        @(posedge clk); #1;
        if( ram_q !== 8'd0 ) begin
            $display("FAIL: address %0d retained %02x after reset", address, ram_q);
            $fatal(1);
        end
    end
endtask

initial begin
    repeat(2) @(posedge clk);

    // Model dirty work RAM from an interrupted game.
    for( i=0; i<DEPTH; i=i+1 ) begin
        @(negedge clk);
        cpu_addr = i[AW-1:0];
        cpu_data = 8'h80 + i[7:0];
        cpu_we   = 1'b1;
    end
    @(negedge clk) cpu_we = 1'b0;

    // Link2P holds game reset much longer than one complete scrub pass.
    @(negedge clk) rst = 1'b1;
    repeat(DEPTH+2) @(posedge clk);
    @(negedge clk) rst = 1'b0;
    #1;

    if( clear_we !== 1'b0 ) begin
        $display("FAIL: clear write remained active after reset");
        $fatal(1);
    end

    for( i=0; i<DEPTH; i=i+1 ) read_zero(i[AW-1:0]);

    // Normal game writes must regain the port after recovery.
    @(negedge clk);
    cpu_addr = 4'd7;
    cpu_data = 8'h5a;
    cpu_we   = 1'b1;
    @(negedge clk) cpu_we = 1'b0;
    @(posedge clk); #1;
    if( ram_q !== 8'h5a ) begin
        $display("FAIL: CPU RAM access did not resume after scrub");
        $fatal(1);
    end

    $display("PASS: Link2P reset scrubs dirty JTBUBL RAM and returns the port");
    $finish;
end

endmodule
