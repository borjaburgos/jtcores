`timescale 1ns/1ps

// Exact packet-tail corruption reproduced by the 5 ms outage phase sweep.
// CRC-8 accepted this damaged packet; CRC-32 must reject the same damaged
// payload with an all-one received checksum. Fixed independent vectors also
// prevent the transmitter and receiver from sharing an unnoticed CRC error.
module link2p_crc_tb;
parameter CRC_BITS=32;
localparam PACKET_BITS=216+CRC_BITS;
localparam [215:0] BODY=216'h4c320246835f6d005cbb955aa1268a90e42beb5005a05b005ab70e;
localparam [CRC_BITS-1:0] CHECKSUM=CRC_BITS==32 ? 32'hf1c70159 : 32'h15;
reg clk=0, rst=1, sck=0, si=1;
always #5 clk=~clk;
wire [PACKET_BITS-1:0] received;
wire valid, crc_ok;
reg last_crc=0;
integer packets=0;

jtframe_pocket_link_serial #(
    .HOST(0), .PACKET_BITS(PACKET_BITS), .CRC_BITS(CRC_BITS),
    .HALF_DIV(8), .GAP_CYCLES(24), .GAP_DETECT(12)
) dut (
    .clk(clk), .rst(rst), .tx_packet({PACKET_BITS{1'b1}}),
    .rx_packet(received), .rx_valid(valid), .rx_crc_ok(crc_ok),
    .serial_in(si), .sck_in(sck), .serial_out(), .sck_out(),
    .sck_oe(), .slot_active()
);

always @(posedge clk) if(valid) begin
    packets=packets+1;
    last_crc=crc_ok;
end

task clocks(input integer n);
    repeat(n) @(negedge clk);
endtask
task send(input [PACKET_BITS-1:0] packet);
    integer count_before;
    count_before=packets;
    clocks(32);
    for(integer bitpos=PACKET_BITS-1;bitpos>=0;bitpos--) begin
        si=packet[bitpos]; clocks(8);
        sck=1; clocks(8); sck=0;
    end
    clocks(32);
    if(packets!=count_before+1 || received!==packet)
        $fatal(1,"packet framing error");
endtask

initial begin
    clocks(10); rst=0;
    send({BODY,CHECKSUM});
    if(!last_crc) $fatal(1,"known CRC vector rejected");
    send({BODY,CHECKSUM} | {{197{1'b0}}, {(19+CRC_BITS){1'b1}}});
    if(last_crc !== (CRC_BITS==8))
        $fatal(1,"CRC-%0d collision regression failed",CRC_BITS);
    // Clock loss with SO stuck low can deliver an all-zero packet. Legacy
    // CRC-8 starts at zero and accepts it; production CRC-32 must reject it.
    send({PACKET_BITS{1'b0}});
    if(last_crc !== (CRC_BITS==8))
        $fatal(1,"CRC-%0d zero-packet regression failed",CRC_BITS);
    $display("PASS CRC-%0d fixed vector, packet-tail corruption, and zero packet",CRC_BITS);
    $finish;
end
initial begin
    #1000000;
    $fatal(1,"CRC regression timeout");
end
endmodule
