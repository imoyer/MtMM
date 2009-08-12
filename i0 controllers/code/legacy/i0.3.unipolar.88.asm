;
; i0.3.unipolar.88
; i0 three-wire I/O node demonstration code
; IPv4 version
; 2-16-2 encoding
;
; Neil Gershenfeld
; CBA MIT 11/30/08
; 
; (c) Massachusetts Institute of Technology 2008
; Permission granted for experimental and personal use;
; license for commercial sale available from MIT.
;
.include "m88def.inc"

;
; definitions
;

;stepper motor

.equ phase1a	=	PC3
.equ phase1b	=	PC2
.equ phase2a	=	PC1
.equ phase2b	=	PC0
.equ motorport	=	PORTC
.equ motordirection = DDRC

;stepping sequences



.equ normal1			=	0b00001000
.equ normal2			=	0b00000010
.equ normal3			=	0b00000100
.equ normal4			=	0b00000001
	
.equ half1			=	0b00001000
.equ half2			=	0b00001010
.equ half3			=	0b00000010
.equ half4			=	0b00000110
.equ half5			=	0b00000100
.equ half6			=	0b00000101
.equ half7			=	0b00000001
.equ half8			=	0b00001001
	
.equ power1			=	0b00001010
.equ power2			=	0b00001001
.equ power3			=	0b00000101
.equ power4			=	0b00000110

;end stepper motor

.equ direction_mask	=	0b00000001
.equ stepmode_mask	=	0b00000110

.equ motor_forward	=	0b00000000
.equ motor_reverse	=	0b00000001

.equ normalstep_config		=	0b00000000
.equ halfstep_config		=	0b00000010
.equ powerstep_config		=	0b00000100

;network ports

.equ config_port = 890; motor configuration port
.equ sync_port = 727; motor sync port
.equ Web_port = 80 ; Web server port
.equ set_source_address_port = 1000 ; port to set board's source address
.equ set_destination_address_port = 1001 ; port to set board's destination address 
.equ toggle_port = 1002 ; port to toggle the light

;end network ports

.equ set_destination_flag = 1 ; status flag for setting destination address
.equ set_source_flag = 2 ; status flag for setting source address
.equ click_pin = PB0 ; PA0 to PB2 i0 click pin
.equ click_port = PORTB
.equ click_direction = DDRB
.equ click_input = PINB
.equ click_count = 5 ; loop count to wait during click
.equ settle_count = 5 ; loop count to wait for click to settle
.equ delay_count = 10 ; loop count to wait between clicks
.equ char_delay_count = 15 ; loop count for character delay
.equ csma_count = 20 ; loop count for CSMA check
.equ button_bit = PD5 ; button bit
;.equ button_pin = PD5  not sure

.equ button_port = PORTD ;button output port
.equ button_direction = DDRD; button direction port
.equ button_input = PIND ;button input port
.equ button_pin = PD5 ; button pin

.equ LED_port = PORTD ;LED output port
.equ LED_direction = DDRD ;LED direction port
.equ LED_pin = PD6 ; LED input port


.equ END = 192 ; SLIP definitions
.equ ESC = 219 ; "
.equ ESC_END = 220 ; "
.equ ESC_ESC = 221 ; "
.equ eeprom_source_address = 0 ; EEPROM addresses
.equ eeprom_destination_address = eeprom_source_address + 4 ; "
;
; registers
;
.def zero = R1 ; 0
.def one = R2 ; 1
.def double_count = R3 ; double loop count
.def triple_space = R4 ; triple click spacing
.def check_lo = R5 ; lo checksum accumulator
.def check_hi = R6 ; hi checksum accumulator
.def check_carry = R7 ; checksum carry accumulator
.def motor_configuration = r8 ; configuration for stepper motor, i.e. forward-reverse
.def duration_0 = r9 ; counts until end of move
.def duration_1 = r10
.def command_travel_0 = r11
.def command_travel_1 = r12
.def current_travel_0 = r13
.def current_travel_1 = r14
.def motor_position = r15 ; keeps track of current position in phase table


.def bit_count = R16 ; bit counter
.def byte_count = R17 ; byte counter
.def txbyte = R18 ; transmit byte
.def rxbyte = R19 ; receive byte
.def temp = R20 ; temporary storage
.def temp1 = R21 ; temporary storage
.def temp2 = R22 ; temporary storage
.def temp3 = R23 ; temporary storage
.def flags = R24 ; status flags
.def click_space = R25 ; click spacing
.def count = R26 ; loop counter (X low)
.def count_hi = R27 ; loop counter (X high)



; R28, 29 used for Y pointer
; R30, 31 used for Z pointer
;

;.def count2 = R08
;.def tempH = R13
;.def tempH1 = R14

; macros
;
; copy
;
.macro copy
   ;
   ; copy bytes between two memory locations
   ; copy destination, source
   ;
   ldi zh, high(@1)
   ldi zl, low(@1)
   ld temp, z
   ldi zh, high(@0)
   ldi zl, low(@0)
   st z, temp
   .endmacro
;
; compare
;
.macro compare
   ;
   ; compare two memory locations
   ;
   ldi zh, high(@1)
   ldi zl, low(@1)
   ld temp, z
   ldi zh, high(@0)
   ldi zl, low(@0)
   ld temp1, z
   cp temp, temp1
   .endmacro
;
; compare_immediate
;
.macro compare_immediate
   ;
   ; compare memory location with a constant
   ;
   ldi zh, high(@0)
   ldi zl, low(@0)
   ld temp, z
   cpi temp, @1
   .endmacro
;
; store_immediate
;
.macro store_immediate
   ;
   ; store immediate constant to memory
   ;
   ldi temp, @1
   sts @0, temp
   .endmacro
;
; set_data
;
.macro set_data
   ;
   ; set Y registers to point to data
   ;
   ldi yh, high(@0*2)
   ldi yl, low(@0*2)
   .endmacro
;
; putslip
;
.macro putslip
   ;
   ; putslip
   ; click char in txbyte, with SLIP mapping
   ;
   ldi temp, END
   cpse txbyte, temp
   rjmp putslipchar
      ;
      ; END char
      ;
      mov temp, txbyte
      ldi txbyte, ESC
      rcall putclick
      rcall char_delay
      ldi txbyte, ESC_END
      rcall putclick
      rcall char_delay
      mov txbyte, temp
      rjmp endputslip
   ldi temp, ESC
   cpse txbyte, temp
   rjmp putslipchar
      ;
      ; ESC char
      ;
      mov temp, txbyte
      ldi txbyte, ESC
      rcall putclick
      rcall char_delay
      ldi txbyte, ESC_ESC
      rcall putclick
      rcall char_delay
      mov txbyte, temp
      rjmp endputslip
   putslipchar:
      ;
      ; ordinary char, no escape needed
      ;
      rcall putclick
      rcall char_delay
   endputslip:
      .endmacro
;
; read_eeprom
;
.macro read_eeprom
   ;
   ; read EEPROM location to register
   ;
   read_eeprom_loop: ; make sure EEPROM is ready for writing
      sbic EECR, EEPE
         rjmp read_eeprom_loop
   ldi temp, high(@1)
   out EEARH, temp
   ldi temp, low(@1)
   out EEARL, temp
   sbi EECR, EERE
   in @0, EEDR
   .endmacro
;
; write_eeprom
;
.macro write_eeprom
   ;
   ; write register to EEPROM
   ;
   write_eeprom_loop: ; make sure EEPROM is ready for writing
      sbic EECR, EEPE
         rjmp write_eeprom_loop
   cbi EECR, EEPM1
   cbi EECR, EEPM0
   ldi temp, high(@0)
   out EEARH, temp
   ldi temp, low(@0)
   out EEARL, temp
   out EEDR, @1
   sbi EECR, EEMPE
   sbi EECR, EEPE
   .endmacro
;
; write_sram_to_eeprom
;
.macro write_sram_to_eeprom
   ;
   ; write SRAM location to EEPROM
   ;
   write_sram_to_eeprom_loop: ; make sure EEPROM is ready for writing
      sbic EECR, EEPE
         rjmp write_sram_to_eeprom_loop
   cbi EECR, EEPM1
   cbi EECR, EEPM0
   ldi temp, high(@0)
   out EEARH, temp
   ldi temp, low(@0)
   out EEARL, temp
   ldi zh, high(@1)
   ldi zl, low(@1)
   ld temp, z
   out EEDR, temp
   sbi EECR, EEMPE
   sbi EECR, EEPE
   .endmacro
;
; code segment
;
.cseg
.org 0

;--INTERRUPT VECTOR TABLE----------------------------------------------------------

    rjmp    reset                           ; External Pin, Power-on Reset, Brown-out Reset and Watchdog
    .dw     0                               ; External Interrupt Request 0 
    .dw     0                               ; External Interrupt Request 1
    .dw     0                               ; Pin Change Interrupt Request 0
    .dw     0                               ; Pin Change Interrupt Request 1
    .dw     0	                            ; Pin Change Interrupt Request 2
    .dw     0	 			               	; Watchdog Time-out Interrupt
    .dw		0			                    ; Timer/Counter2 Compare Match A
    .dw     0		                    	; Timer/Counter2 Compare Match B
    .dw     0                               ; Timer/Counter2 Overflow
    .dw     0                               ; Timer/Counter1 Capture Event
    .dw     0			                    ; Timer/Counter1 Compare Match A
    .dw     0		                   		; Timer/Coutner1 Compare Match B
    .dw     0                               ; Timer/Counter1 Overflow
    rjmp    motor_update			    ; Timer/Counter0 Compare Match A
    .dw     0                               ; Timer/Counter0 Compare Match B
    .dw     0                               ; Timer/Counter0 Overflow
	.dw		0								; SPI Serial Transfer Complete
	.dw		0								; USART Rx Complete
	.dw		0								; USART, Data Register Empty
	.dw		0								; USART, Tx Complete
	.dw		0								; ADC Conversion Complete
	.dw		0								; EEPROM Ready
	.dw		0								; Analog Comparator
	.dw		0								; 2-wire Serial Interface
	.dw		0								; Store Program Memory Ready


;
;motor update
;

motor_update:
	cli

	push temp1  ; store variables
    in temp1, SREG
    push temp1
    push temp2
	push zh
	push zl

	cp duration_0, zero ; check whether move is over
	  brne motor_update_200
	cp duration_1, zero
	  brne motor_update_200
	rjmp motor_update_exit

motor_update_200:

	add current_travel_0, one
	adc current_travel_1, zero

	cp current_travel_0, command_travel_0 ; check whether step is generated
	  brne motor_update_exit
	cp current_travel_1, command_travel_1
	  brne motor_update_exit
	
motor_update_300:

		;tun on led
   in temp, LED_port
   ldi temp1, (1 << LED_pin) 
   eor temp, temp1
   out LED_port, temp

	clr current_travel_0
	clr current_travel_1

	ldi temp1, direction_mask
	mov temp2, motor_configuration
	and temp2, temp1
	breq motor_step_forward

motor_step_reverse:
	dec motor_position
	ldi temp1, 255
	cp motor_position, temp1
	brne motor_update_400
	ldi temp1, 7
	mov motor_position, temp1
	rjmp motor_update_400
	
motor_step_forward:
	inc motor_position
	ldi temp1, 8
	cp motor_position, temp1
	brne motor_update_400
	mov motor_position, zero

motor_update_400:
    ldi ZL, low(halfstep*2)
    ldi ZH, high(halfstep*2)
    add ZL, motor_position
    adc ZH, zero
    lpm temp1, Z

	out motorport, temp1

motor_update_500:
	sub duration_0, one
	sbc duration_1, zero

	cp duration_1, zero
	  brne motor_update_exit
	cp duration_0, zero
	  brne motor_update_exit

motor_end_of_move:
	ldi     temp1, (0 << OCIE0B)|(0 << OCIE0A)|(0 << TOIE0)		;diable timer0 interrupts
    sts     TIMSK0, TEMP1

motor_update_exit:
	sei
	pop zl
	pop zh
	pop temp2
	pop temp1
	out SREG, temp1
	pop temp1
	
	reti

; init_packet
; initialize outgoing packet in SRAM
;
init_packet:
   .equ ip_header_size = 20
   .equ ip_header_size_before_checksum = 10
   .equ ip_header_size_after_checksum = 8
   .equ udp_header_size = 8
   .equ outgoing_ip_start = SRAM_START;
   .equ outgoing_ip_length = outgoing_ip_start + 2
   .equ outgoing_ip_checksum = outgoing_ip_start + 10
   .equ outgoing_source_address = outgoing_ip_start + 12
   .equ outgoing_destination_address = outgoing_ip_start + 16
   .equ outgoing_udp_start = outgoing_ip_start + 20
   .equ outgoing_source_port = outgoing_udp_start
   .equ outgoing_destination_port = outgoing_udp_start + 2
   .equ outgoing_udp_length = outgoing_udp_start + 4
   ldi zl, low(outgoing_ip_start)
   ldi zh, high(outgoing_ip_start)
   ;
   ; IP
   ;
   ldi temp, 0x45 ; version = 4 (4 bits), header length = 5 32-bit words (4 bits)
      st z+, temp
   ldi temp, 0 ; type of service
      st z+, temp
   ldi temp, 0 ; packet length high byte (to be calculated)
      st z+, temp
   ldi temp, 0 ; packet length low byte (to be calculated)
      st z+, temp
   ldi temp, 0 ; identification (high byte)
      st z+, temp
   ldi temp, 0 ; identification (low byte)
      st z+, temp
   ldi temp, 0 ; flag (3 bits), fragment offset (13 bits) (high byte)
      st z+, temp
   ldi temp, 0 ; flag (3 bits), fragment offset (13 bits) (low byte)
      st z+, temp
   ldi temp, 255 ; time to live
      st z+, temp
   ldi temp, 17 ; protocol = 17 for UDP
      st z+, temp
   ldi temp, 0 ; header checksum (to be calculated)
      st z+, temp
   ldi temp, 0 ; header checksum (to be calculated)
      st z+, temp
   read_eeprom temp, eeprom_source_address ; source address byte 1
     st z+, temp
   read_eeprom temp, eeprom_source_address+1 ; source address byte 2
     st z+, temp
   read_eeprom temp, eeprom_source_address+2 ; source address byte 3
     st z+, temp
   read_eeprom temp, eeprom_source_address+3 ; source address byte 4
     st z+, temp
   read_eeprom temp, eeprom_destination_address ; destination address byte 1
     st z+, temp
   read_eeprom temp, eeprom_destination_address+1 ; destination address byte 2
     st z+, temp
   read_eeprom temp, eeprom_destination_address+2 ; destination address byte 3
     st z+, temp
   read_eeprom temp, eeprom_destination_address+3 ; destination address byte 4
     st z+, temp
   ;
   ; UDP
   ;
   ldi temp, 0 ; source port
      st z+, temp
   ldi temp, 0 ; source port
      st z+, temp
   ldi temp, 0 ; destination port
      st z+, temp
   ldi temp, 0 ; destination port
      st z+, temp
   ldi temp, 0 ; payload length high byte (to be calculated)
      st z+, temp
   ldi temp, 0 ; payload length low byte (to be calculated)
      st z+, temp
   ldi temp, 0 ; payload checksum (not used)
      st z+, temp
   ldi temp, 0 ; payload checksum (not used)
      st z+, temp
   ;
   ; null-terminated data messages
   ;
   empty_message:
      .db 0
   on_message:
      .db "HTTP/1.1 200 OK",13,10,"Content-Type: text/html",13,10,13,10,"<center><H1>motor turned X times and light is on",13,10,0
   off_message:
      .db "HTTP/1.1 200 OK",13,10,"Content-Type: text/html",13,10,13,10,"<center><H1>motor turned X times and light is off",13,10,0
   ret   
;
; get_I0_packet
; read an I0 packet to SRAM following starting SLIP END character,
; removing SLIP mapping
;
get_packet:
   .equ incoming_start = outgoing_ip_start + ip_header_size + udp_header_size
   .equ incoming_source_address = incoming_start + 12
   .equ incoming_destination_address = incoming_source_address + 4
   .equ incoming_destination_port = incoming_destination_address + 6
   .equ incoming_data = incoming_destination_port + 6
   ;
   ; set Z to point to start of SRAM
   ;
   ldi zl, low(incoming_start)
   ldi zh, high(incoming_start)
   clr byte_count
   get_packet_mainloop:
      ;
      ; wait for a click
      ;
      clr count
      ldi count_hi, 1
      get_packet_waitloop:
         add count, one
	      adc count_hi, zero
            breq get_packet_timeout ; time-out if loop count overflows
         sbic click_input, click_pin ; check i0 pin for click
	         rjmp get_packet_waitloop
      ;
      ; read next byte
      ;
      rcall getclick
      ;
      ; return if byte count overflows
      ;
      inc byte_count
         breq get_packet_timeout
      ;
      ; check for SLIP escape
      ;
      cpi rxbyte, ESC
      brne get_packet_store_byte
         ;
	      ; found escape, read next character after next click
	      ;
         get_packet_waitloop1:
            sbic click_input, click_pin ; check i0 pin for click
	            rjmp get_packet_waitloop1
         rcall getclick
	      cpi rxbyte, ESC_ESC
	      brne get_packet_END
	      ;
	      ; store an ESC
	      ;
	      ldi rxbyte, ESC
         st z+, rxbyte
	      rjmp get_packet_mainloop
	get_packet_END:
	   ;
	   ; store an END
	   ;
	   ldi rxbyte, END
      st z+, rxbyte
	   rjmp get_packet_mainloop
      ;
      ; store byte
      ;
      get_packet_store_byte:
         st z+, rxbyte
      ;
      ; go back for next byte if not END
      ;
      ldi temp, END
      cpse rxbyte, temp
         rjmp get_packet_mainloop
      ret
   get_packet_timeout:
      clr byte_count
      ret
;
; click_duration
; delay during click
;
click_duration:
   ldi temp, click_count
   click_duration_loop:
      dec temp
      brne click_duration_loop
   ret
;
; click_delay
; delay between clicks
;
click_delay:
   ldi temp, delay_count
   click_delay_loop:
      dec temp
      brne click_delay_loop
   ret
;
; putclick
; send char in txbyte clicks
;
putclick:
   ldi bit_count, 8
   sec; set start bit
   ;
   ; set click pin to output
   ;
   sbi click_direction, click_pin
   ;
   ; send start clicks
   ;
   cbi click_port, click_pin
   rcall click_duration
   sbi click_port, click_pin
   rcall click_delay
   cbi click_port, click_pin
   rcall click_duration
   sbi click_port, click_pin
   rcall click_delay
   ;
   ; send data clicks
   ;
   putclick0:
      lsr txbyte; get next bit
         brcc putclick1 ; if carry set, send a 1 click
      cbi click_port, click_pin
      rcall click_duration
      sbi click_port, click_pin
      rcall click_delay
      sbi click_port, click_pin
      rcall click_duration
      sbi click_port, click_pin
      rcall click_delay
      rjmp putclick2; otherwise ...
   putclick1:
      sbi click_port, click_pin ; ... send a 0 click
      rcall click_duration
      sbi click_port, click_pin
      rcall click_delay
      cbi click_port, click_pin
      rcall click_duration
      sbi click_port, click_pin
      rcall click_delay
   putclick2:
      dec bit_count; if not all bits sent
      brne putclick0; send next bit
   ;
   ; send stop clicks
   ;
   cbi click_port, click_pin
   rcall click_duration
   sbi click_port, click_pin
   rcall click_delay
   cbi click_port, click_pin
   rcall click_duration
   sbi click_port, click_pin
   rcall click_delay
   ;
   ; set click pin to input with pull-up
   ;
   cbi click_direction, click_pin
   ;
   ; return
   ;
   ret
;
; getclick
; input an i0 byte following first click
;
getclick:
   ;
   ; delay for first click to settle
   ;
   ldi count, settle_count
   getclick_settle_start:
      dec count
      nop ; to even out timing for breq
      brne getclick_settle_start
   ;
   ; time arrivial of second start click
   ;
   ldi click_space, (settle_count+1) ; +1 for overhead
   getclick_time_start:
      inc click_space
         breq getclick_timeout ; check for overflow
      sbic click_input, click_pin ; check for click
         rjmp getclick_time_start
   mov triple_space, click_space
   add triple_space, click_space
   add triple_space, click_space
   ;
   ; decode data clicks
   ;
   clr rxbyte
   ldi bit_count, 8
   getclick_bitloop:
      ;
      ; delay for click to settle
      ;
      ldi count, settle_count
      getclick_settle:
         dec count
         nop ; to even out timing for breq
         brne getclick_settle
      ;
      ; time arrivial of next click
      ;
      ldi count, settle_count
      getclick_time:
         inc count
         breq getclick_timeout ; check for overflow
         sbic click_input, click_pin ; check for click
            rjmp getclick_time
      ;
      ; determine bit delay
      ;
      mov double_count, count
      add double_count, count
      cp double_count, triple_space
      brsh getclick_zero
         ;
         ; one bit
         ;
         sec ; set carry
         ror rxbyte ; shift in carry
                                                                                                               
;
         ; even out 0/1 timing
         ;
         mov count, click_space
         getclick_space:
            dec count
            nop ; to even out timing for breq
            brne getclick_space
	      ;
	      ; decrement counter and output if byte received
	      ;
         dec bit_count
      	brne getclick_bitloop
   	      rjmp getclick_end
      getclick_zero:
         ;
         ; zero bit
         ; 
         clc ; clear carry
	      ror rxbyte ; shift in carry
	      ;
	      ; decrement counter and output if byte received
	      ;
         dec bit_count
         brne getclick_bitloop
      getclick_end:
         ;
	      ; wait for stop clicks and return
	      ;
         getclick_end_0_up:
            sbis click_input, click_pin
	       rjmp getclick_end_0_up
         getclick_end_1_down:
            sbic click_input, click_pin
	       rjmp getclick_end_1_down
         getclick_end_1_up:
            sbis click_input, click_pin
	       rjmp getclick_end_1_up
         getclick_end_2_down:
            sbic click_input, click_pin
	       rjmp getclick_end_2_down
         getclick_end_2_up:
            sbis click_input, click_pin
	       rjmp getclick_end_2_up
      	 ret
      getclick_timeout:
         ldi rxbyte, 0
	      ret
;
; char_delay
; delay between characters
;
char_delay:
   ldi temp, char_delay_count
   char_delay_loop:
      dec temp
      brne char_delay_loop
   ret
;
; packet_delay
; delay between packets
;
packet_delay:
   ldi temp, 255
   packet_delayloop:
      ldi temp1, 255
      packet_delayloop1:
         dec temp1
         brne packet_delayloop1
      dec temp
      brne packet_delayloop
   ret
;
; print_packet
; send a packet, calculating header checksum and doing SLIP encoding
; Y registers point to data
;
print_packet:
   ;
   ; count data length and store in packet
   ;
   mov zl, yl
   mov zh, yh
   clr count
   clr count_hi
   count_data_loop:
      adiw count, 1
      lpm temp, z+
      cpi temp, 0
      brne count_data_loop
   sbiw count,1 ; don't count the null termination
   adiw count, udp_header_size
   sts outgoing_udp_length, count_hi
   sts outgoing_udp_length+1, count
   adiw count, ip_header_size
   sts outgoing_ip_length, count_hi
   sts outgoing_ip_length+1, count
   ;
   ; find the IP header checksum and store in packet
   ;
   ldi zh, high(outgoing_ip_start)
   ldi zl, low(outgoing_ip_start)
   ldi count, ip_header_size
   clr check_lo
   clr check_hi
   clr check_carry
   ip_checksum_loop:
      adiw zl, 1
      ld temp, z
      dec count
      sbiw zl, 1
      ld temp1, z
      add check_lo, temp
      adc check_hi, temp1
      adc check_carry, zero
      adiw zl, 2
      dec count
      brne ip_checksum_loop
   add check_lo, check_carry
   adc check_hi, zero
   com check_lo
   com check_hi
   sts outgoing_ip_checksum, check_hi
   sts outgoing_ip_checksum+1, check_lo
   ;
   ; CSMA check
   ;
   print_packet_CSMA:
      ldi temp, csma_count
	   print_packet_CSMA_loop:
         sbis click_input, click_pin
            rjmp print_packet_CSMA_delay
         dec temp
	      brne print_packet_CSMA_loop
            rjmp print_packet_CSMA_continue
      print_packet_CSMA_delay:
         ldi temp, csma_count
	      print_packet_CSMA_delay_loop:
            dec temp
	         brne print_packet_CSMA_delay_loop
         rjmp print_packet_CSMA
      print_packet_CSMA_continue:
   ;
   ; send the packet
   ;
   ldi txbyte, END ; SLIP start
   rcall putclick
   rcall char_delay
   ldi zh, high(outgoing_ip_start)
   ldi zl, low(outgoing_ip_start)
   ldi count, (ip_header_size + udp_header_size)
   print_header_loop: ; IP + UDP header
      ld txbyte, z
      putslip
      adiw zl, 1
      dec count
      brne print_header_loop
   mov zl, yl
   mov zh, yh
   print_data_loop: ; data
      lpm txbyte, z+
      cpi txbyte, 0
         breq print_data_continue
      putslip
      rjmp print_data_loop
   print_data_continue:
   ldi txbyte, END ; SLIP end
   rcall putclick
   rcall char_delay
   ret
;
; handle button actions
;
button_pressed:
   ;
   ; is there a pending set source packet?
   ; 
   sbrc flags, set_source_flag
      rjmp button_pressed_set_source_address
   ;
   ; is there a pending set destination packet?
   ; 
   sbrc flags, set_destination_flag
      rjmp button_pressed_set_destination_address
   ;
   ; is the destination address not set?
   ;
   compare_immediate outgoing_destination_address, 255
      breq button_pressed_send_set_destination
   rjmp button_pressed_send_packet
   ;
   ; otherwise send a set destination packet
   ;
   button_pressed_send_set_destination:
      ;
      ; blink the light to acknowledge
      ;
      rcall blink
      rcall blink
      ;
      ; set up and send set destination packet
      ;
      store_immediate outgoing_source_port, high(set_destination_address_port)
      store_immediate outgoing_source_port+1, low(set_destination_address_port)
      store_immediate outgoing_destination_port, high(set_destination_address_port)
      store_immediate outgoing_destination_port+1, low(set_destination_address_port)
      set_data(empty_message)
      rcall print_packet
      ret
   button_pressed_set_source_address:
      ;
      ; blink the light to acknowledge
      ;
      rcall blink
      rcall blink
      ;
      ; set source address to destination address from last received packet
      ;
      copy outgoing_source_address, incoming_destination_address
      copy outgoing_source_address+1, incoming_destination_address+1
      copy outgoing_source_address+2, incoming_destination_address+2
      copy outgoing_source_address+3, incoming_destination_address+3
      ;
      ; save source address to EEPROM
      ;
      write_sram_to_eeprom eeprom_source_address, outgoing_source_address
      write_sram_to_eeprom eeprom_source_address+1, outgoing_source_address+1
      write_sram_to_eeprom eeprom_source_address+2, outgoing_source_address+2
      write_sram_to_eeprom eeprom_source_address+3, outgoing_source_address+3
      ;
      ; clear flags and return
      ;
      clr flags
      ret
   button_pressed_set_destination_address:
      ;
      ; blink the light to acknowledge
      ;
      rcall blink
      rcall blink
      ;
      ; set destination address to source address from last received packet
      ;
      copy outgoing_destination_address, incoming_source_address
      copy outgoing_destination_address+1, incoming_source_address+1
      copy outgoing_destination_address+2, incoming_source_address+2
      copy outgoing_destination_address+3, incoming_source_address+3
      ;
      ; save destination address to EEPROM
      ;
      write_sram_to_eeprom eeprom_destination_address, outgoing_destination_address
      write_sram_to_eeprom eeprom_destination_address+1, outgoing_destination_address+1
      write_sram_to_eeprom eeprom_destination_address+2, outgoing_destination_address+2
      write_sram_to_eeprom eeprom_destination_address+3, outgoing_destination_address+3
      ;
      ; clear flags and return
      ;
      clr flags
      ret
   button_pressed_send_packet:
      ;
      ; blink the light to acknowledge
      ;
      rcall blink
      ;
      ; set up and send toggle packet
      ;
      store_immediate outgoing_source_port, high(toggle_port)
      store_immediate outgoing_source_port+1, low(toggle_port)
      store_immediate outgoing_destination_port, high(toggle_port)
      store_immediate outgoing_destination_port+1, low(toggle_port)
      set_data(empty_message)
      rcall print_packet
      ret
;
; blink the light
;
blink:
   in temp, PORTD
   ldi temp1, (1 << LED_pin)
   eor temp, temp1
   out PORTD, temp
   rcall packet_delay
   in temp, PORTD
   ldi temp1, (1 << LED_pin) 
   eor temp, temp1
   out PORTD, temp
   rcall packet_delay
   ret
;
; send the Web page
;
send_Web_page:
   ;
   ; blink the light to acknowledge
   ;
   rcall blink
   rcall blink
   ;
   ; set up and send Web page
   ;
   store_immediate outgoing_source_port, high(Web_port)
   store_immediate outgoing_source_port+1, low(Web_port)
   store_immediate outgoing_destination_port, high(Web_port)
   store_immediate outgoing_destination_port+1, low(Web_port)
   sbic LED_port, LED_pin
      rjmp Web_send_on
   Web_send_off:
      set_data(off_message)
      rjmp Web_send_continue
   Web_send_on:
      set_data(on_message)
   Web_send_continue:
      rcall print_packet
   ret
;
; toggle the light
;
toggle_light:
   in temp, LED_port
   ldi temp1, (1 << LED_pin)
   eor temp, temp1
   out LED_port, temp
   ret
;
; main program
;
reset:
   ;
   ; set fuse low byte to 0x7E for 20 MHz resonator
   ;
   ; set clock divider to /1
   ;
   ldi temp, (1 << CLKPCE)
   ldi temp1, (0 << CLKPS3) | (0 << CLKPS2) | (0 << CLKPS1) | (0 << CLKPS0)
   sts CLKPR, temp
   sts CLKPR, temp1
   ;
   ; set stack pointer to top of RAM
   ;
   ldi temp, high(RAMEND)
   out SPH, temp
   ldi temp, low(RAMEND)
   out SPL, temp

   ;configure timer0 for stepper motor control
   
 ;CONFIGURE TIMER0
    
    ldi     temp1, (0 << COM0A1)|(0 << COM0A0)|(0 << COM0B1)|(0 << COM0B0)|(1 << WGM01)|(0 <<WGM00)	;configures timer0 as CTC
    out     TCCR0A, TEMP1

    ldi     temp1, (0 << FOC0A)|(0 << FOC0B)|(0 << WGM02)|(1 << CS02)|(0 << CS01)|(1 << CS00)	;configures prescaler as clk/1024
    out     TCCR0B, TEMP1
 

   ;configure motor port
   ;
   ldi temp1, (1<< phase1a)|(1<<phase1b)|(1<<phase2a)|(1<<phase2b)
   out motordirection, temp1


   ;
   ; init click pin for input with pull-up
   ;
   sbi click_port, click_pin
   cbi click_direction, click_pin
   ;
   ; init button for input with pull-up
   ;
   sbi button_port, button_pin
   cbi button_direction, button_pin
   ;cbi button_port, button_gnd
   ;sbi button_direction, button_gnd
   ;
   ; init LED for output
   ;
   cbi LED_port, LED_pin
   sbi LED_direction, LED_pin

   ;

   ;
   ; init registers
   ;
   clr zero ; 0
   clr one ; 1
   inc one ; "
   clr motor_position
   ;
   ; set source address if not assigned
   ;
   read_eeprom temp, eeprom_source_address
   cpi temp, 255
      brne source_address_assigned
   source_address_not_assigned:
      ;
      ; turn on light, start counter, and wait for button to be pressed
      ;
      sbi LED_port, LED_pin
      clr temp1
      clr temp2
      clr temp3
      source_address_not_assigned_loop:
         add temp1, one
   	   adc temp2, zero
	      adc temp3, zero
         sbic button_input, button_bit					
            rjmp source_address_not_assigned_loop
      ;
      ; wait for button to be released
      ;
      source_address_not_button_release:
         sbis button_input, button_bit					
            rjmp source_address_not_button_release
      ;
      ; move address to EEPROM, acknowledge and turn off light
      ;
      ; hardcode 11.1.1.1

	;ldi temp1, 1
	;ldi temp2, 1
	;ldi temp3, 1



      write_eeprom eeprom_source_address+3, temp1
      write_eeprom eeprom_source_address+2, temp2
      write_eeprom eeprom_source_address+1, temp3
      ldi temp1, 169
      write_eeprom eeprom_source_address, temp1
      rcall blink
      rcall blink
      cbi LED_port, LED_pin
   source_address_assigned:
      ;
      ; init the packet
      ;
      rcall init_packet
   ;
   ; start event loop
   ;
   clr flags ; clear status flags
   mainloop:



      ;
      ; wait for the button to be pressed or a click to arrive
      ;
      waitloop:
         sbis click_input, click_pin ; check i0 pin for click
            rjmp click
         sbic button_input, button_bit ; check for button
            rjmp waitloop
      ;
      ; button pressed
      ;
      button:
         ;
         ; wait for button to be released
         ;
         button_release:
            sbis button_input, button_bit
               rjmp button_release
	      rcall button_pressed
 






         rjmp mainloop
      ;
      ; click arrived
      ;
      click:
	      ;
	      ; check for i0 SLIP start of packet (END character)
	      ;
          cli
	      rcall getclick
	      ldi temp, END
	      cpse rxbyte, temp
       ;
	    ; not start of packet, go back and wait for next char
	    ;
	    rjmp mainloop
    ;
	 ; found start, get rest of i0 packet
	 ;
    rcall get_packet
	 ;
	 ; return to mainloop if byte_count is zero
	 ;
	 tst byte_count
	    breq mainloop
	 ;
	 ; valid packet received, check for address assignment packets
	 ;
	 clr flags ; clear status flags
	 check_set_destination_address_port:
	    compare_immediate incoming_destination_port, high(set_destination_address_port)
	       brne check_set_source_address_port
	    compare_immediate incoming_destination_port+1, low(set_destination_address_port)
	       brne check_set_source_address_port
	    sbr flags, (1 << set_destination_flag)
	    rcall blink
	    rcall blink
       rjmp mainloop
	 check_set_source_address_port:
	    compare_immediate incoming_destination_port, high(set_source_address_port)
	       brne check_sync
	    compare_immediate incoming_destination_port+1, low(set_source_address_port)
	       brne check_sync
            sbr flags, (1 << set_source_flag)
	    rcall blink
	    rcall blink
       rjmp mainloop

     ;
     ; check to see if incoming port is the sync port
     ;
     check_sync:
	     compare_immediate incoming_destination_port, high(sync_port)
	        brne check_address
	     compare_immediate incoming_destination_port+1, low(sync_port)
	        brne check_address
         rjmp move_enable
	 ;
	 ; check to see if incoming destination address matches
	 ;

	 check_address:
	    mainloop_test_1:
 	       compare outgoing_source_address, incoming_destination_address
	       breq mainloop_test_2
	          rjmp mainloop
	    mainloop_test_2:
	       compare outgoing_source_address+1, incoming_destination_address+1
	       breq mainloop_test_3
	          rjmp mainloop
	    mainloop_test_3:
	       compare outgoing_source_address+2, incoming_destination_address+2
	       breq mainloop_test_4
	          rjmp mainloop
	    mainloop_test_4:
	       compare outgoing_source_address+3, incoming_destination_address+3
	       breq address_matches
	          rjmp mainloop
    ;
	 ; address matches, check port
	 ;
	 address_matches:
	    check_Web_port:
	       compare_immediate incoming_destination_port, high(Web_port)
	          brne check_toggle_port
	       compare_immediate incoming_destination_port+1, low(Web_port)
	          brne check_toggle_port
	       rcall send_Web_page
          rjmp mainloop
	    check_toggle_port:
	       compare_immediate incoming_destination_port, high(toggle_port)
	          brne check_config_port
	       compare_immediate incoming_destination_port+1, low(toggle_port)
	          brne check_config_port
	       ;rcall toggle_light
               rcall turn_on_motor
          rjmp mainloop
	    check_config_port:
	       compare_immediate incoming_destination_port, high(config_port)
	          brne port_not_assigned
	       compare_immediate incoming_destination_port+1, low(config_port)
	          brne port_not_assigned
	       ;rcall move_config
               rcall move_config
          rjmp mainloop
		   
       port_not_assigned:
	       rjmp mainloop

move_config:

	clr current_travel_0 ; clear move-specific registers
	clr current_travel_1

	ldi zh, high(incoming_data) ; Stores move command from i0 packet to registers
	ldi zl, low(incoming_data)
	ld temp1, Z+
	out OCR0A, temp1
	ld temp1, Z+
	mov command_travel_0, temp1
	ld temp1, Z+
	mov command_travel_1, temp1
	ld temp1, Z+
	mov duration_0, temp1
	ld temp1, Z+
	mov duration_1, temp1
	ld temp1, Z+
	mov motor_configuration, temp1
  

	in temp, LED_port
    ldi temp1, (1 << LED_pin) 
    eor temp, temp1
    out LED_port, temp



	ret


turn_on_motor:

;tun on led
   in temp, LED_port
   ldi temp1, (1 << LED_pin) 
   eor temp, temp1
   out LED_port, temp

nop
nop
;rjmp mainloop
ret

move_enable:

    ldi     temp1, (0 << OCIE0B)|(1 << OCIE0A)|(0 << TOIE0)		;enable timer0 interrupts
    sts     TIMSK0, TEMP1
	
	clr temp1
	out TCNT0, temp1 ; clear timer0
	
	sei ; enable global interrupts

	rjmp mainloop

;--STEPPING MAP-------------------------------------------------------------------

normalstep:
    .db     normal4, normal3
    .db     normal2, normal1
	.db		0, 0
	.db		0, 0

powerstep:
    .db     power1, power2
    .db     power3, power4
	.db		0, 0
	.db		0, 0
	
halfstep:
	.db		half1, half2
	.db		half3, half4
	.db		half5, half6
	.db		half7, half8











