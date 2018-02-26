import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import browser from 'detect-browser';

import { AboutModal } from 'patternfly-react';

import logo from '../../styles/images/Red_Hat_logo.svg';
import productTitle from '../../styles/images/title.svg';

const About = ({ user, shown, onClose }) => {
  return (
    <AboutModal
      key="aboutModal"
      show={shown}
      onHide={onClose}
      productTitle={<img src={productTitle} alt="Red Hat Entitlements Reporting" />}
      logo={logo}
      altLogo="RH ER"
      trademarkText="Copyright (c) 2018 Red Hat Inc."
    >
      <AboutModal.Versions>
        <AboutModal.VersionItem label="Sonar Version" versionText="0.1" />
        <AboutModal.VersionItem label="Username" versionText={_.get(user, 'currentUser.username', '')} />
        <AboutModal.VersionItem
          label="Browser Version"
          versionText={`${_.get(browser, 'name', '')} ${_.get(browser, 'version', '')}`}
        />
        <AboutModal.VersionItem label="Browser OS" versionText={_.get(browser, 'os', '')} />
      </AboutModal.Versions>
    </AboutModal>
  );
};

About.propTypes = {
  user: PropTypes.object,
  shown: PropTypes.bool,
  onClose: PropTypes.func
};
export default About;
