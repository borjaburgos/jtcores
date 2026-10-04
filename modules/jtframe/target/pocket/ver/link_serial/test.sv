`timescale 1ns/1ps

// Independent endpoint clocks and an exact-packet scoreboard. The DUT owns
// framing and receive CRC only; the test supplies complete transmit packets.
module test;
parameter CRC_BITS=32;
parameter HALF_DIV=96;
parameter real JOIN_HALF_NS=10.418;
localparam PACKET_BITS=CRC_BITS==32 ? 248 : 192;
localparam SLOT_CLKS=HALF_DIV*(2*PACKET_BITS+8);
reg hclk=0, jclk=0, hrst=1, jrst=1;
always #10.416667 hclk=~hclk;
initial begin
    #3.137;
    forever #(JOIN_HALF_NS) jclk=~jclk;
end

reg [PACKET_BITS-1:0] htx, jtx, expected_h, expected_j;
wire [PACKET_BITS-1:0] hrx, jrx;
wire hvalid, jvalid, hcrc, jcrc, hso, jso, sck, hoe, joe, ha, ja;
reg flip_h=0, flip_j=0, drop_h=0, drop_j=0, drop_sck=0, clock_level=0;
reg allow_bad=0;
integer good_h=0, good_j=0, bad_h=0, bad_j=0;
reg last_hvalid=0, last_jvalid=0;
reg [PACKET_BITS-1:0] last_hrx=0, last_jrx=0;

jtframe_pocket_link_serial #(
    .HOST(1), .PACKET_BITS(PACKET_BITS), .CRC_BITS(CRC_BITS),
    .HALF_DIV(HALF_DIV), .GAP_CYCLES(8*HALF_DIV), .GAP_DETECT(4*HALF_DIV)
) host (
    .clk(hclk), .rst(hrst), .tx_packet(htx), .rx_packet(hrx),
    .rx_valid(hvalid), .rx_crc_ok(hcrc), .serial_in(drop_h ? 1'b1 : jso^flip_h),
    .sck_in(1'b0), .serial_out(hso), .sck_out(sck), .sck_oe(hoe), .slot_active(ha)
);
jtframe_pocket_link_serial #(
    .HOST(0), .PACKET_BITS(PACKET_BITS), .CRC_BITS(CRC_BITS),
    .HALF_DIV(HALF_DIV), .GAP_CYCLES(8*HALF_DIV), .GAP_DETECT(4*HALF_DIV)
) joiner (
    .clk(jclk), .rst(jrst), .tx_packet(jtx), .rx_packet(jrx),
    .rx_valid(jvalid), .rx_crc_ok(jcrc), .serial_in(drop_j ? 1'b1 : hso^flip_j),
    .sck_in(drop_sck ? clock_level : sck), .serial_out(jso), .sck_out(),
    .sck_oe(joe), .slot_active(ja)
);

always @(posedge ha) expected_h=htx;
always @(posedge ja) expected_j=jtx;
always @(negedge hclk) begin
    if (!hrst) begin
        if (hvalid && last_hvalid) $fatal(1,"Host rx_valid is not a pulse");
        if (!hvalid && (hcrc || hrx!==last_hrx)) $fatal(1,"Host receive changed outside rx_valid");
    end
    last_hvalid=hvalid; last_hrx=hrx;
end
always @(negedge jclk) begin
    if (!jrst) begin
        if (jvalid && last_jvalid) $fatal(1,"Join rx_valid is not a pulse");
        if (!jvalid && (jcrc || jrx!==last_jrx)) $fatal(1,"Join receive changed outside rx_valid");
    end
    last_jvalid=jvalid; last_jrx=jrx;
end
always @(negedge hclk) if (!hrst && hvalid) begin
    if (hcrc) begin
        if (hrx!==expected_j)
            $fatal(1,"Host CRC-%0d accepted wrong packet: got=%h expected=%h",CRC_BITS,hrx,expected_j);
        good_h=good_h+1;
    end else begin
        if (!allow_bad) $fatal(1,"Unexpected Host checksum failure");
        bad_h=bad_h+1;
    end
end
always @(negedge jclk) if (!jrst && jvalid) begin
    if (jcrc) begin
        if (jrx!==expected_h)
            $fatal(1,"Join CRC-%0d accepted wrong packet: got=%h expected=%h",CRC_BITS,jrx,expected_h);
        good_j=good_j+1;
    end else begin
        if (!allow_bad) $fatal(1,"Unexpected Join checksum failure");
        bad_j=bad_j+1;
    end
end

function [PACKET_BITS-1:0] packet(input integer seed);
    reg [PACKET_BITS-1:0] word_value;
    reg [CRC_BITS-1:0] crc, polynomial;
    reg feedback;
    integer i;
    begin
        word_value=0;
        crc=CRC_BITS'(CRC_BITS==32 ? 32'hffffffff : 0);
        polynomial=CRC_BITS'(CRC_BITS==32 ? 32'h04c11db7 : 32'h07);
        for (i=PACKET_BITS-1; i>=CRC_BITS; i=i-1) begin
            word_value[i]=(((i*13+seed)>>(i%7)) & 1)!=0;
            feedback=crc[CRC_BITS-1]^word_value[i];
            crc=crc<<1;
            if (feedback) crc=crc^polynomial;
        end
        word_value[CRC_BITS-1:0]=crc;
        packet=word_value;
    end
endfunction

task clocks(input integer count);
    repeat(count) @(negedge hclk);
endtask
task clean_slots(input integer count);
    integer target_h, target_j, remaining;
    begin
        target_h=good_h+count;
        target_j=good_j+count;
        remaining=(count+3)*SLOT_CLKS;
        while (good_h<target_h || good_j<target_j) begin
            clocks(1);
            remaining=remaining-1;
            if (remaining==0) $fatal(1,"Did not recover within %0d slots",count+3);
        end
    end
endtask
task at_bit(input integer bitpos);
    begin
        wait(!ha);
        wait(ha);
        wait(int'(host.bit_count)==bitpos && !sck);
        @(negedge hclk);
    end
endtask

task corrupt_bit(input integer bitpos);
    integer before_h, before_j;
    begin
        at_bit(bitpos);
        before_h=bad_h; before_j=bad_j;
        allow_bad=1; flip_h=1; flip_j=1;
        clocks(2*HALF_DIV);
        flip_h=0; flip_j=0;
        clean_slots(2);
        if (bad_h!=before_h+1 || bad_j!=before_j+1)
            $fatal(1,"Bit %0d: corruption count H=%0d J=%0d",bitpos,bad_h-before_h,bad_j-before_j);
        allow_bad=0;
    end
endtask

task interrupt_wire(input integer direction, input integer bitpos);
    begin
        at_bit(bitpos);
        allow_bad=1;
        drop_h=(direction==0 || direction==1);
        drop_j=(direction==0 || direction==2);
        drop_sck=(direction==0 || direction>=3);
        clock_level=(direction==4);
        clocks(3*SLOT_CLKS+HALF_DIV/2);
        drop_h=0; drop_j=0; drop_sck=0;
        clean_slots(3);
        allow_bad=0;
        $display("PASS wire interruption mode=%0d bit=%0d",direction,bitpos);
    end
endtask

initial begin
    htx=packet(17); jtx=packet(59);
    clocks(10); hrst=0; jrst=0;
    clean_slots(3);
    if (!hoe || joe) $fatal(1,"Wrong clock output direction");

    // Publishing a new packet during a slot must not tear the old packet.
    at_bit(PACKET_BITS/2);
    htx=packet(83); jtx=packet(127);
    clean_slots(3);
    $display("PASS full duplex, asynchronous clocks, and atomic transmit snapshot");

    // Changing complete payloads exercises the scoreboard beyond one fixture.
    for (integer seed=0; seed<12; seed=seed+1) begin
        at_bit(PACKET_BITS/2);
        htx=packet(seed*31+3); jtx=packet(seed*47+7);
        clean_slots(3);
    end

    for (integer bitpos=0; bitpos<PACKET_BITS; bitpos=bitpos+1)
        corrupt_bit(bitpos);
    $display("PASS all %0d packet bits corrupted in both directions",PACKET_BITS);
    // Contact loss can produce all-zero packets, valid under legacy CRC-8.
    // crc_test covers that limitation explicitly; continuation checks here
    // apply to production CRC-32, never to the weaker legacy checksum.
    if (CRC_BITS==32) begin
        for (integer direction=0; direction<5; direction=direction+1) begin
            interrupt_wire(direction,1);
            interrupt_wire(direction,PACKET_BITS/2);
            interrupt_wire(direction,PACKET_BITS-2);
        end

        // Each endpoint can reset independently while the other is mid-slot.
        at_bit(PACKET_BITS/2);
        allow_bad=1; jrst=1; clocks(17); jrst=0;
        clean_slots(3); allow_bad=0;
        at_bit(PACKET_BITS/2);
        allow_bad=1; hrst=1; clocks(17); hrst=0;
        clean_slots(3); allow_bad=0;
        $display("PASS independent mid-slot endpoint resets");
    end
    $display("PASS transport CRC=%0d HALF_DIV=%0d JOIN_HALF_NS=%0f good=%0d/%0d rejected=%0d/%0d",
        CRC_BITS,HALF_DIV,JOIN_HALF_NS,good_h,good_j,bad_h,bad_j);
    $finish;
end

initial begin
    clocks((4*PACKET_BITS+100)*SLOT_CLKS);
    $fatal(1,"Transport test timed out");
end
endmodule
