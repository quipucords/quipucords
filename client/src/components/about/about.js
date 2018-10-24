import React from 'react';
import PropTypes from 'prop-types';
import { detect } from 'detect-browser';
import { AboutModal } from 'patternfly-react';
import _ from 'lodash';
import helpers from '../../common/helpers';
import logo from '../../styles/images/logo.svg';
import productTitle from '../../styles/images/title.svg';
import rhLogo from '../../styles/images/brand/logo.svg';
import rhProductTitle from '../../styles/images/brand/title.svg';

const About = ({ user, status, shown, onClose }) => {
  const versionText = `${_.get(status, 'api_version', 'unknown')} (Build: ${_.get(status, 'build', 'unknown')})`;
  const browser = detect();

  const props = {
    show: shown,
    onHide: onClose,
    logo,
    productTitle: <img src={productTitle} alt="Entitlements Reporting" />,
    altLogo: 'ER'
  };

  if (helpers.RH_BRAND) {
    props.logo = rhLogo;
    props.productTitle = <img src={rhProductTitle} alt="Red Hat Entitlements Reporting" />;
    props.altLogo = 'RH ER';
    props.trademarkText = 'Copyright (c) 2018 Red Hat Inc.';
  }

  return (
    <AboutModal {...props}>
      <AboutModal.Versions>
        <AboutModal.VersionItem label="Version" versionText={versionText} />
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
  status: PropTypes.object,
  shown: PropTypes.bool,
  onClose: PropTypes.func
};

About.defaultProps = {
  user: {},
  status: {},
  shown: false,
  onClose: helpers.noop
};

export { About as default, About };
