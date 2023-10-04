"""Unit tests for initial processing."""


from scanner.network.processing import brms
from scanner.network.processing.util_for_test import (
    ansible_item,
    ansible_result,
    ansible_results,
)


class TestProcessJbossBRMSManifestMF:
    """Test ProcessJbossBRMSManifestMF."""

    # This is a portion of the BRMS 6.4.0 MANIFEST.MF
    MANIFEST = """Manifest-Version: 1.0
Implementation-Title: KIE Drools Workbench - Distribution Wars
Implementation-Version: 6.5.0.Final-redhat-2
"""

    def test_success(self):
        """Extract the Implementation_Version from a manifest."""
        assert brms.ProcessJbossBRMSManifestMF.process_item(
            ansible_item("/opt/brms/", self.MANIFEST)
        ) == ("/opt/brms", "6.5.0.Final-redhat-2")

    def test_no_version(self):
        """Don't crash if the manifest is missing a version."""
        assert (
            brms.ProcessJbossBRMSManifestMF.process_item(
                ansible_item("manifest", "not\na\nmanifest")
            )
            is None
        )


class TestEnclosingWarArchive:
    """Test enclosing_war_archive."""

    def test_enclosing(self):
        """Return the enclosing war archive."""
        assert (
            brms.enclosing_war_archive("/foo/kie-server.war/bar/baz")
            == "/foo/kie-server.war"
        )

    def test_war_root(self):
        """Return the war archive when applied to just the archive."""
        assert (
            brms.enclosing_war_archive("/foo/kie-server.war") == "/foo/kie-server.war"
        )

    def test_no_war_archive(self):
        """Return None when there is no war archive."""
        assert brms.enclosing_war_archive("/foo/bar/baz") is None


class TestProcessJbossBRMSKieBusinessCentral:
    """Test ProcessJbossBRMSKieBusinessCentral."""

    good_result = {
        "item": "/path/to/good/",
        "stdout": "/path/to/good/kie-api-version-string.jar-1234",
        "rc": 0,
    }
    bad_result = {"item": "/path/to/bad/", "stdout": "", "rc": 1}
    ls_results = ansible_results([good_result, bad_result])

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        assert set(
            brms.ProcessJbossBRMSKieBusinessCentral.process(self.ls_results)
        ) == {("/path/to/good", "version-string")}


class TestFindBRMSKieApiVer:
    """Test FindBRMSKieApiVer."""

    ansible_stdout = (
        "/opt/jboss/jboss-eap-6.4/standalone/deployments/business-central.war/"
        "WEB-INF/lib/kie-api-6.5.0.Final-redhat-2.jar\r\n"
        "/opt/jboss/jboss-eap-6.4/standalone/deployments/kie-server.war/"
        "WEB-INF/lib/kie-api-6.5.0.Final-redhat-2.jar\r\n"
    )

    expected = {
        (
            "/opt/jboss/jboss-eap-6.4/standalone/deployments/business-central.war",
            "6.5.0.Final-redhat-2",
        ),
        (
            "/opt/jboss/jboss-eap-6.4/standalone/deployments/kie-server.war",
            "6.5.0.Final-redhat-2",
        ),
    }

    def test_success_case(self):
        """Return the correct (directory, version string) pairs."""
        assert (
            set(
                brms.ProcessFindBRMSKieApiVer.process(
                    ansible_result(self.ansible_stdout)
                )
            )
            == self.expected
        )


class TestProcessFindBRMSKieWarVer:
    """Test ProcessFindBRMSKieWarVer."""

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        assert brms.ProcessFindBRMSKieWarVer.process(ansible_result("a\nb\nc")) == [
            "a",
            "b",
            "c",
        ]


class TestProcessJbossBRMSBusinessCentralCandidates:
    """Test using locate to find kie server candidates."""

    def test_success(self):
        """Found jboss-modules.jar."""
        assert brms.ProcessJbossBRMSBusinessCentralCandidates.process(
            "QPC_FORCE_POST_PROCESS",
            {
                "internal_jboss_brms_business_central_candidates": ansible_result(
                    "a\nb\nc"
                )
            },
        ) == ["a", "b", "c"]

    def test_not_found(self):
        """Did not find jboss-modules.jar."""
        assert (
            brms.ProcessJbossBRMSBusinessCentralCandidates.process(
                "QPC_FORCE_POST_PROCESS",
                {"internal_jboss_brms_business_central_candidates": ansible_result("")},
            )
            == []
        )


class TestProcessJbossBRMSDecisionCentralCandidates:
    """Test using locate to find decision candidates."""

    def test_success(self):
        """Found candidates."""
        assert brms.ProcessJbossBRMSDecisionCentralCandidates.process(
            "QPC_FORCE_POST_PROCESS",
            {
                "internal_jboss_brms_decision_central_candidates": ansible_result(
                    "a\nb\nc"
                )
            },
        ) == ["a", "b", "c"]

    def test_not_found(self):
        """Did not find candidates."""
        assert (
            brms.ProcessJbossBRMSDecisionCentralCandidates.process(
                "QPC_FORCE_POST_PROCESS",
                {"internal_jboss_brms_decision_central_candidates": ansible_result("")},
            )
            == []
        )


class TestProcessJbossBRMSKieCentralCandidates:
    """Test using locate to find kie server candidates."""

    def test_success(self):
        """Found candidates."""
        assert brms.ProcessJbossBRMSKieCentralCandidates.process(
            "QPC_FORCE_POST_PROCESS",
            {"internal_jboss_brms_kie_server_candidates": ansible_result("a\nb\nc")},
        ) == ["a", "b", "c"]

    def test_not_found(self):
        """Did not find candidates."""
        assert (
            brms.ProcessJbossBRMSKieCentralCandidates.process(
                "QPC_FORCE_POST_PROCESS",
                {"internal_jboss_brms_kie_server_candidates": ansible_result("")},
            )
            == []
        )


class TestProcessKieSearchCandidates:
    """Test using locate to find kie server candidates."""

    def test_success(self):
        """Found candidates."""
        assert brms.ProcessKieSearchCandidates.process(
            "QPC_FORCE_POST_PROCESS",
            {"internal_jboss_brms_kie_server_candidates": ansible_result("a\nb\nc")},
        ) == ["a", "b", "c"]

    def test_not_found(self):
        """Did not find candidates."""
        assert (
            brms.ProcessKieSearchCandidates.process(
                "QPC_FORCE_POST_PROCESS",
                {"internal_jboss_brms_kie_server_candidates": ansible_result("")},
            )
            == []
        )
