import time

class TestSflow:
    speed_rate_table = {
        "400000": "400000",
        "200000": "200000",
        "100000": "100000",
        "50000": "50000",
        "40000": "40000",
        "25000": "25000",
        "10000": "10000",
        "1000": "1000"
    }

    def setup_sflow(self, dvs):
        self.adb = dvs.get_asic_db()
        self.cdb = dvs.get_config_db()

        self.cdb.create_entry("SFLOW", "global", {"admin_state": "up"})

    def test_defaultGlobal(self, dvs, testlog):
        self.setup_sflow(dvs)

        # Verify that the session is up
        port_oid = self.adb.port_name_map["Ethernet0"]
        expected_fields = {"SAI_PORT_ATTR_INGRESS_SAMPLEPACKET_ENABLE": "oid:0x0"}
        fvs = self.adb.wait_for_field_negative_match("ASIC_STATE:SAI_OBJECT_TYPE_PORT", port_oid, expected_fields)

        sample_session = fvs["SAI_PORT_ATTR_INGRESS_SAMPLEPACKET_ENABLE"]
        speed = fvs["SAI_PORT_ATTR_SPEED"]

        rate = self.speed_rate_table.get(speed, None)
        assert rate

        expected_fields = {"SAI_SAMPLEPACKET_ATTR_SAMPLE_RATE": rate}
        self.adb.wait_for_field_match("ASIC_STATE:SAI_OBJECT_TYPE_SAMPLEPACKET", sample_session, expected_fields)

        self.cdb.update_entry("SFLOW", "global", {"admin_state": "down"})
        expected_fields = {"SAI_PORT_ATTR_INGRESS_SAMPLEPACKET_ENABLE": "oid:0x0"}
        self.adb.wait_for_field_match("ASIC_STATE:SAI_OBJECT_TYPE_PORT", port_oid, expected_fields)

    def test_globalAll(self, dvs, testlog):
        self.setup_sflow(dvs)

        # Verify that the session is up first
        port_oid = self.adb.port_name_map["Ethernet0"]
        expected_fields = {"SAI_PORT_ATTR_INGRESS_SAMPLEPACKET_ENABLE": "oid:0x0"}
        self.adb.wait_for_field_negative_match("ASIC_STATE:SAI_OBJECT_TYPE_PORT", port_oid, expected_fields)

        # Then shut down the session
        self.cdb.update_entry("SFLOW_SESSION", "all", {"admin_state": "down"})
        expected_fields = {"SAI_PORT_ATTR_INGRESS_SAMPLEPACKET_ENABLE": "oid:0x0"}
        self.adb.wait_for_field_match("ASIC_STATE:SAI_OBJECT_TYPE_PORT", port_oid, expected_fields)

        self.cdb.update_entry("SFLOW_SESSION", "all", {"admin_state": "up"})
        self.adb.wait_for_field_negative_match("ASIC_STATE:SAI_OBJECT_TYPE_PORT", port_oid, expected_fields)

        self.cdb.delete_entry("SFLOW_SESSION", "all")
        self.adb.wait_for_field_negative_match("ASIC_STATE:SAI_OBJECT_TYPE_PORT", port_oid, expected_fields)

    def test_InterfaceSet(self, dvs, testlog):
        self.setup_sflow(dvs)

        # Get the global session info as a baseline
        port_oid = self.adb.port_name_map["Ethernet0"]
        expected_fields = ["SAI_PORT_ATTR_INGRESS_SAMPLEPACKET_ENABLE"]
        fvs = self.adb.wait_for_fields("ASIC_STATE:SAI_OBJECT_TYPE_PORT", port_oid, expected_fields)
        global_session = fvs["SAI_PORT_ATTR_INGRESS_SAMPLEPACKET_ENABLE"]

        # Then create the interface session
        session_params = {"admin_state": "up", "sample_rate": "1000"}
        self.cdb.create_entry("SFLOW_SESSION", "Ethernet0", session_params)

        # Verify that the new interface session has been created and is different from the global one
        port_oid = self.adb.port_name_map["Ethernet0"]
        expected_fields = {"SAI_PORT_ATTR_INGRESS_SAMPLEPACKET_ENABLE": global_session}
        fvs = self.adb.wait_for_field_negative_match("ASIC_STATE:SAI_OBJECT_TYPE_PORT", port_oid, expected_fields)

        sample_session = fvs["SAI_PORT_ATTR_INGRESS_SAMPLEPACKET_ENABLE"]

        expected_fields = {"SAI_SAMPLEPACKET_ATTR_SAMPLE_RATE": "1000"}
        self.adb.wait_for_field_match("ASIC_STATE:SAI_OBJECT_TYPE_SAMPLEPACKET", sample_session, expected_fields)

        self.cdb.create_entry("SFLOW_SESSION", "all", {"admin_state": "down"})

        expected_fields = {"SAI_PORT_ATTR_INGRESS_SAMPLEPACKET_ENABLE": "oid:0x0"}
        self.adb.wait_for_field_negative_match("ASIC_STATE:SAI_OBJECT_TYPE_PORT", port_oid, expected_fields)

        self.cdb.create_entry("SFLOW", "global", {"admin_state": "down"})
        self.adb.wait_for_field_match("ASIC_STATE:SAI_OBJECT_TYPE_PORT", port_oid, expected_fields)

        self.cdb.delete_entry("SFLOW_SESSION", "all")
        self.cdb.delete_entry("SFLOW_SESSION", "Ethernet0")

    def test_defaultRate(self, dvs, testlog):
        self.setup_sflow(dvs)

        session_params = {"admin_state": "up"}
        self.cdb.create_entry("SFLOW_SESSION", "Ethernet4", session_params)

        port_oid = self.adb.port_name_map["Ethernet4"]
        expected_fields = {"SAI_PORT_ATTR_INGRESS_SAMPLEPACKET_ENABLE": "oid:0x0"}
        fvs = self.adb.wait_for_field_negative_match("ASIC_STATE:SAI_OBJECT_TYPE_PORT", port_oid, expected_fields)

        sample_session = fvs["SAI_PORT_ATTR_INGRESS_SAMPLEPACKET_ENABLE"]
        speed = fvs["SAI_PORT_ATTR_SPEED"]

        rate = self.speed_rate_table.get(speed, None)
        assert rate

        expected_fields = {"SAI_SAMPLEPACKET_ATTR_SAMPLE_RATE": rate}
        self.adb.wait_for_field_match("ASIC_STATE:SAI_OBJECT_TYPE_SAMPLEPACKET", sample_session, expected_fields)

        self.cdb.delete_entry("SFLOW_SESSION", "Ethernet4")

    def test_ConfigDel(self, dvs, testlog):
        self.setup_sflow(dvs)

        session_params = {"admin_state": "up", "sample_rate": "1000"}
        self.cdb.create_entry("SFLOW_SESSION_TABLE", "Ethernet0", session_params)

        self.cdb.delete_entry("SFLOW_SESSION_TABLE", "Ethernet0")

        port_oid = self.adb.port_name_map["Ethernet0"]
        expected_fields = {"SAI_PORT_ATTR_INGRESS_SAMPLEPACKET_ENABLE": "oid:0x0"}
        fvs = self.adb.wait_for_field_negative_match("ASIC_STATE:SAI_OBJECT_TYPE_PORT", port_oid, expected_fields)

        sample_session = fvs["SAI_PORT_ATTR_INGRESS_SAMPLEPACKET_ENABLE"]
        speed = fvs["SAI_PORT_ATTR_SPEED"]

        rate = self.speed_rate_table.get(speed, None)
        assert rate

        expected_fields = {"SAI_SAMPLEPACKET_ATTR_SAMPLE_RATE": rate}
        self.adb.wait_for_field_match("ASIC_STATE:SAI_OBJECT_TYPE_SAMPLEPACKET", sample_session, expected_fields)
    
    def test_SamplingRatePortCfgUpdate(self, dvs, testlog):
        '''
        This test checks if the SflowMgr updates the sampling rate 
        1) When the Speed is Updated on the port and no local configuration has been given on the port
        Eg:
        config sflow enable
        config interface speed Ethernet0  25000  (Let's suppose Original Speed for Ethernet0 is 100G)
        show sflow interface | grep Ethernet0    (Should see a sampling rate of 25000 not 100000)
        '''
        self.setup_sflow(dvs)
        appldb = dvs.get_app_db()
        #dvs.runcmd("portconfig -p {} -s {}".format("Ethernet0", "25000"))
        self.cdb.update_entry("PORT", "Ethernet0", {'speed' : "25000"})
        expected_fields = {"sample_rate": self.speed_rate_table["25000"]}
        appldb.wait_for_field_match("SFLOW_SESSION_TABLE", "Ethernet0", expected_fields)

    
    def test_SamplingRateManualUpdate(self, dvs, testlog):
        '''  
        This test checks if the SflowMgr updates the sampling rate 
        1) When the Cfg Sflow Table is updated with sampling rate by the user, this rate should not be impacted by Port Speed Changes
        Eg:
        config sflow enable
        config sflow interface sample-rate Ethernet4 256
        config interface Ethernet0 speed 25000  (Original Speed for Ethernet0 is 100G)
        show sflow interface | grep Ethernet0   (Should see  a sampling rate of 256 not 100000 or 25000
        '''
        self.setup_sflow(dvs)
        appldb = dvs.get_app_db()
        
        session_params = {"admin_state": "up", "sample_rate": "256"}
        self.cdb.create_entry("SFLOW_SESSION", "Ethernet4", session_params)
        self.cdb.wait_for_field_match("SFLOW_SESSION", "Ethernet4", session_params)
        appldb.wait_for_field_match("SFLOW_SESSION_TABLE", "Ethernet4", {"sample_rate": "256"})
        
        self.cdb.update_entry("PORT", "Ethernet4", {'speed' : "25000"})
        # The Check here is about the original value not getting changed. 
        # If some bug was to appear, let's give it some time to get noticed
        time.sleep(1) 
        appldb.wait_for_field_match("SFLOW_SESSION_TABLE", "Ethernet4", {"sample_rate": "256"})
    

    def test_Teardown(self, dvs, testlog):
        self.setup_sflow(dvs)

        self.cdb.delete_entry("SFLOW", "global")
        self.adb.wait_for_n_keys("ASIC_STATE:SAI_OBJECT_TYPE_SAMPLEPACKET", 0)


# Add Dummy always-pass test at end as workaroud
# for issue when Flaky fail on final test it invokes module tear-down before retrying
def test_nonflaky_dummy():
    pass
