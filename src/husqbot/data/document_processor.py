"""
Document processing for Husqvarna RAG Support System.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ManualChunk:
    """Represents a chunk of manual content."""
    id: str
    section: str
    subsection: str
    content: str
    page_number: int
    chunk_type: str
    manual_type: str = "owners"


class DocumentProcessor:
    """Processes Husqvarna manual documents into chunks."""
    
    def __init__(self):
        """Initialize the document processor."""
        self.chunk_size = 1000  # characters
        self.chunk_overlap = 200  # characters
        
    async def process_manual(
        self, 
        file_path: str, 
        manual_type: str = "owners"
    ) -> List[ManualChunk]:
        """
        Process a manual PDF file into chunks.
        
        Args:
            file_path: Path to the PDF file
            manual_type: Type of manual (owners, repair)
            
        Returns:
            List of manual chunks
        """
        logger.info(f"Processing manual: {file_path}")
        
        # For now, return the pre-extracted chunks
        # In a full implementation, this would parse the PDF
        if manual_type == "owners":
            return self._get_owners_manual_chunks()
        elif manual_type == "repair":
            return self._get_repair_manual_chunks()
        else:
            raise ValueError(f"Unknown manual type: {manual_type}")
    
    def _get_owners_manual_chunks(self) -> List[ManualChunk]:
        """Get pre-extracted chunks from the Husqvarna 701 Enduro Owner's Manual."""
        
        chunks_data = [
            {
                "id": "safety_001",
                "section": "2 SAFETY ADVICE",
                "subsection": "2.1 Use definition – intended use",
                "content": "The vehicle is designed and constructed to withstand the usual demands of regular traffic and use on gentle terrain (unpaved roads). This vehicle is not suitable for use on race tracks. This vehicle is only authorized for operation on public roads in its homologated version.",
                "page_number": 6,
                "chunk_type": "safety"
            },
            {
                "id": "safety_002",
                "section": "2 SAFETY ADVICE", 
                "subsection": "2.12 Safe operation",
                "content": "Danger of accidents: A rider who is not fit to ride poses a danger to him or herself and others. Do not operate the vehicle if you are not fit to ride due to alcohol, drugs or medication. Do not operate the vehicle if you are physically or mentally impaired. Danger of poisoning: Exhaust gases are toxic and inhaling them may result in unconsciousness and death. Always make sure there is sufficient ventilation when running the engine.",
                "page_number": 11,
                "chunk_type": "warning"
            },
            {
                "id": "start_001",
                "section": "9 RIDING INSTRUCTIONS",
                "subsection": "9.2 Starting the vehicle",
                "content": "Turn the emergency OFF switch to the position. Switch on the ignition by turning the ignition key to the ON position. To avoid malfunctions in the control unit communication, do not switch the ignition off and on in rapid succession. Shift the transmission to neutral position. Green idle indicator lamp N lights up. Press start button. Do not press the start button until the combination instrument function check has finished. Do not open the throttle to start.",
                "page_number": 35,
                "chunk_type": "procedure"
            },
            {
                "id": "engine_oil_001",
                "section": "18 SERVICE WORK ON THE ENGINE",
                "subsection": "18.2 Checking the engine oil level", 
                "content": "Condition: The engine is at operating temperature. Stand the motorcycle upright on a horizontal surface. Check the engine oil level. After switching off the engine, wait one minute before checking the level. The engine oil must be between marking A and marking B of the oil level viewer. If the engine oil level is below the B mark: Add engine oil. If the engine oil level is above the A mark: Correct the engine oil level.",
                "page_number": 109,
                "chunk_type": "procedure"
            },
            {
                "id": "engine_oil_002",
                "section": "18 SERVICE WORK ON THE ENGINE",
                "subsection": "18.3 Changing the engine oil and oil filter",
                "content": "Warning: Danger of scalding - Engine and gear oil get hot when the motorcycle is operated. Wear suitable protective clothing and safety gloves. Drain the engine oil while the engine is at operating temperature. Remove filler plug with the O-ring. Remove oil drain plug with the magnet and seal ring. Allow the engine oil to drain completely. Engine oil capacity: 1.70 l (1.8 qt.) Engine oil (SAE 10W/50).",
                "page_number": 109,
                "chunk_type": "procedure"
            },
            {
                "id": "tire_specs_001",
                "section": "22 TECHNICAL SPECIFICATIONS",
                "subsection": "22.4 Chassis",
                "content": "Tire pressure, road, solo: front 1.8 bar (26 psi), rear 1.8 bar (26 psi). Tire pressure with passenger/full payload: front 2.2 bar (32 psi), rear 2.2 bar (32 psi). Tire pressure, offroad, solo: front 1.5 bar (22 psi), rear 1.5 bar (22 psi). Maximum permissible overall weight: 350 kg (772 lb.). Maximum permissible front axle load: 150 kg (331 lb.). Maximum permissible rear axle load: 200 kg (441 lb.).",
                "page_number": 125,
                "chunk_type": "specification"
            },
            {
                "id": "fuel_specs_001",
                "section": "22 TECHNICAL SPECIFICATIONS", 
                "subsection": "22.3.3 Fuel",
                "content": "Fuel tank capacity, approx. 12.4 l (3.28 US gal) Super unleaded (ROZ 95). Fuel reserve, approx. 1.4 l (1.5 qt.). Only use super unleaded fuel that matches or is equivalent to the specified standard. Fuel with an ethanol content of up to 10% (E10 fuel) is safe to use. Do not use fuel containing methanol or more than 10% ethanol.",
                "page_number": 125,
                "chunk_type": "specification"
            },
            {
                "id": "chain_tension_001",
                "section": "12 SERVICE WORK ON THE CHASSIS",
                "subsection": "12.23 Checking the chain tension",
                "content": "Warning: Danger of accidents - Incorrect chain tension damages components and results in accidents. If the chain is tensioned too much, the chain, engine sprocket, rear sprocket, transmission and rear wheel bearings wear more quickly. If the chain is too loose, the chain may fall off the engine sprocket or the rear sprocket. Push the chain upward at a distance B from the chain sliding guard and determine chain tension A. Chain tension A: 5 mm (0.2 in). Distance B to chain sliding guard: 30 mm (1.18 in). The top part of chain C must be taut.",
                "page_number": 60,
                "chunk_type": "procedure"
            },
            {
                "id": "brake_fluid_001",
                "section": "13 BRAKE SYSTEM",
                "subsection": "13.5 Adding front brake fluid",
                "content": "Warning: Danger of accidents - An insufficient brake fluid level will cause the brake system to fail. If the brake fluid level drops below the specified marking or the specified value, the brake system is leaking or the brake linings are worn down. Warning: Skin irritation - Brake fluid is a harmful substance. Keep brake fluid out of the reach of children. Move the brake fluid reservoir mounted on the handlebar to a horizontal position. Remove screws. Take off cover with membrane. Add brake fluid to level A. Level A (brake fluid level below reservoir rim): 5 mm (0.2 in). Brake fluid DOT 4 / DOT 5.1.",
                "page_number": 69,
                "chunk_type": "procedure"
            },
            {
                "id": "troubleshooting_001",
                "section": "21 TROUBLESHOOTING",
                "subsection": "Engine does not turn when start button is pressed",
                "content": "Faults: The engine does not turn when the start button is pressed. Possible causes: Operating error, 12-V battery discharged, Fuse 1, 2 or 3 blown, Main fuse burned out, No ground connection present. Actions: Carry out start procedure, Charge the 12-V battery, Change the fuses of individual electrical power consumers, Change the main fuse, Check the ground connection.",
                "page_number": 119,
                "chunk_type": "troubleshooting"
            },
            {
                "id": "troubleshooting_002", 
                "section": "21 TROUBLESHOOTING",
                "subsection": "Engine turns but does not start",
                "content": "Faults: Engine turns but does not start. Possible causes: Operating error, Fuse 3 blown, Quick release coupling not joined, Malfunction in the electronic fuel injection, Throttle opened while starting. Actions: Carry out start procedure, Change the fuses of individual electrical power consumers, Join quick release coupling, Read out the fault memory using the Husqvarna Motorcycles diagnostics tool, When starting, DO NOT open the throttle.",
                "page_number": 119,
                "chunk_type": "troubleshooting"
            },
            {
                "id": "troubleshooting_003",
                "section": "21 TROUBLESHOOTING", 
                "subsection": "Engine overheats",
                "content": "Faults: Engine overheats. Possible causes: Too little coolant in cooling system, Radiator fins very dirty, Foam formation in cooling system, Buckled or damaged radiator hose, Thermostat is faulty, Fuse 4 blown, Defect in radiator fan system, Air in cooling system. Actions: Check the cooling system for leakage, Check the coolant level, Clean radiator fins, Drain the coolant and Fill/bleed the cooling system, Change the radiator hose, Check the thermostat, Change the fuses, Check the radiator fan system.",
                "page_number": 119,
                "chunk_type": "troubleshooting"
            },
            {
                "id": "suspension_001",
                "section": "11 TUNING THE CHASSIS",
                "subsection": "11.3 Adjusting the compression damping of the fork",
                "content": "The hydraulic compression damping determines the fork suspension behavior. Turn white adjusting screw clockwise as far as it will go. Adjusting screw is located at the upper end of the left fork leg. Turn counterclockwise by the number of clicks corresponding to the fork type. Compression damping settings: Comfort 20 clicks, Standard 15 clicks, Sport 10 clicks, Full payload 10 clicks. Turn clockwise to increase damping; turn counterclockwise to reduce damping during compression.",
                "page_number": 45,
                "chunk_type": "procedure"
            },
            {
                "id": "suspension_002",
                "section": "11 TUNING THE CHASSIS", 
                "subsection": "11.6 Adjusting the low-speed compression damping of the shock absorber",
                "content": "Caution: Risk of injury - Parts of the shock absorber will move around if the shock absorber is detached incorrectly. The shock absorber is filled with highly compressed nitrogen. The low-speed compression adjuster takes effect during slow to normal compression of the shock absorber. Turn adjusting screw clockwise with a screwdriver as far as the last perceptible click. Do not loosen fitting! Low-speed compression damping settings: Comfort 25 clicks, Standard 20 clicks, Sport 10 clicks, Full payload 10 clicks.",
                "page_number": 47,
                "chunk_type": "procedure"
            },
            {
                "id": "controls_001",
                "section": "6 CONTROLS",
                "subsection": "6.9 Combination switch",
                "content": "The combination switch is fitted on the left side of the handlebar. Possible states: 1 ROAD – Drive mode ROAD and traction control are activated when LED 1 lights up. 1TC ROAD without TC – When LEDs 1 and TC light up, drive mode ROAD is active and traction control is deactivated. 2 OFFROAD – Drive mode OFFROAD and traction control are activated when LED 2 lights up. 2TC OFFROAD without TC – When LEDs 2 and TC light up, drive mode OFFROAD is active and traction control is deactivated.",
                "page_number": 21,
                "chunk_type": "reference"
            },
            {
                "id": "riding_modes_001",
                "section": "17 TUNING THE ENGINE",
                "subsection": "17.1 Changing the riding mode",
                "content": "The desired drive mode can be activated via the MAP button on the combination switch. The setting most recently selected is activated again when restarting. The drive mode can also be changed during the ride. Condition: Throttle grip closed. Press MAP button until the LED displays the desired drive mode. Drive mode 1 is ROAD and drive mode 2 is OFFROAD. ROAD – balanced response. OFFROAD – direct response. The drive mode only influences the throttle response. The homologated performance is available in both drive modes.",
                "page_number": 106,
                "chunk_type": "procedure"
            },
            {
                "id": "abs_001",
                "section": "13 BRAKE SYSTEM",
                "subsection": "13.1 Anti-lock braking system (ABS)",
                "content": "The ABS is a safety system that prevents locking of the wheels when driving straight ahead without the influence of lateral forces. Warning: Danger of accidents - Changes to the vehicle impair the function of the ABS. Do not make any changes to the suspension travel. Only use spare parts on the brake system which have been approved and recommended by Husqvarna Motorcycles. The ABS operates with two independent brake circuits (front and rear brakes). During normal operation, the brake system operates like a conventional brake system without ABS.",
                "page_number": 67,
                "chunk_type": "reference"
            },
            {
                "id": "running_in_001",
                "section": "8 PREPARING FOR USE",
                "subsection": "8.2 Running in the engine",
                "content": "During the running-in time, do not exceed the specified vehicle speed in the respective gear. During the first 1,000 km (620 mi): Maximum speed per gear: first-gear 45 km/h (28 mph), second-gear 65 km/h (40.4 mph), third-gear 85 km/h (52.8 mph), fourth-gear 105 km/h (65.2 mph), fifth-gear 120 km/h (74.6 mph), sixth-gear 130 km/h (80.8 mph). Avoid fully opening the throttle.",
                "page_number": 32,
                "chunk_type": "procedure"
            },
            {
                "id": "service_schedule_001",
                "section": "10 SERVICE SCHEDULE", 
                "subsection": "10.2 Service schedule",
                "content": "Service intervals: after 1,000 km (620 mi), every 10,000 km (6,200 mi), every 20,000 km (12,400 mi), every 30,000 km (18,600 mi), every 12 months, every 24 months, every 48 months. Key service items: Change the engine oil and the oil filter, clean the oil screens. Check that the brake linings of the front brake are secured. Check that the brake linings of the rear brake are secured. Check the brake discs. Check the chain tension. Check tire pressure. Check the tire condition.",
                "page_number": 43,
                "chunk_type": "reference"
            },
            {
                "id": "coolant_001",
                "section": "16 COOLING SYSTEM",
                "subsection": "16.2 Checking the antifreeze and coolant level",
                "content": "Warning: Danger of scalding - During motorcycle operation, the coolant gets hot and is under pressure. Do not open the radiator, the radiator hoses or other cooling system components if the engine or the cooling system are at operating temperature. Condition: The engine is cold. Stand the motorcycle on its side stand on a horizontal surface. Remove cover of the compensating tank. Remove radiator cap. Check the antifreeze in the coolant: −25 … −45 °C (−13 … −49 °F). Check the coolant level in the compensating tank. The coolant level must be between the two markings.",
                "page_number": 100,
                "chunk_type": "procedure"
            }
        ]
        
        return [ManualChunk(**chunk, manual_type="owners") for chunk in chunks_data]
    
    def _get_repair_manual_chunks(self) -> List[ManualChunk]:
        """Get chunks from the repair manual (placeholder for future implementation)."""
        # This would contain repair manual specific chunks
        # For now, return empty list
        return []
    
    def chunk_text(self, text: str, chunk_size: Optional[int] = None) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk (characters)
            
        Returns:
            List of text chunks
        """
        if chunk_size is None:
            chunk_size = self.chunk_size
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start, end - 100), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def classify_chunk_type(self, content: str) -> str:
        """
        Classify the type of content in a chunk.
        
        Args:
            content: Chunk content
            
        Returns:
            Chunk type classification
        """
        content_lower = content.lower()
        
        # Safety and warning detection
        if any(word in content_lower for word in ['danger', 'warning', 'caution', 'risk']):
            return 'warning'
        
        # Procedure detection
        if any(word in content_lower for word in ['step', 'procedure', 'how to', 'instructions']):
            return 'procedure'
        
        # Specification detection
        if any(word in content_lower for word in ['specification', 'capacity', 'pressure', 'temperature']):
            return 'specification'
        
        # Troubleshooting detection
        if any(word in content_lower for word in ['fault', 'problem', 'troubleshooting', 'diagnosis']):
            return 'troubleshooting'
        
        # Reference detection
        if any(word in content_lower for word in ['system', 'component', 'function', 'operation']):
            return 'reference'
        
        return 'general' 