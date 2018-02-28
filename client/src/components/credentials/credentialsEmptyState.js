import React from 'react';
import PropTypes from 'prop-types';

import { Button, DropdownButton, EmptyState, Grid, MenuItem, Row } from 'patternfly-react';

const CredentialsEmptyState = ({ onAddCredential, onAddSource }) => {
  return (
    <Grid fluid>
      <Row>
        <EmptyState className="full-page-blank-slate">
          <EmptyState.Icon />
          <EmptyState.Title>Welcome to Red Hat Entitlements Reporting</EmptyState.Title>
          <EmptyState.Info>
            A credential defines a set of user authentication information to be used during a scan.<br />A credential
            includes a username and a password or SSH key. Entitlements Reporting uses SSH<br />to connect to servers on
            the network and uses credentials to access those servers.
          </EmptyState.Info>
          <EmptyState.Action>
            <DropdownButton
              bsStyle="primary"
              bsSize="large"
              title="Add Credential"
              pullRight
              id="createCredentialButton"
            >
              <MenuItem eventKey="1" onClick={() => onAddCredential('network')}>
                Network Credential
              </MenuItem>
              <MenuItem eventKey="2" onClick={() => onAddCredential('satellite')}>
                Satellite Credential
              </MenuItem>
              <MenuItem eventKey="2" onClick={() => onAddCredential('vcenter')}>
                VCenter Credential
              </MenuItem>
            </DropdownButton>
          </EmptyState.Action>
          <EmptyState.Action secondary>
            <Button bsStyle="default" onClick={onAddSource}>
              Add Source
            </Button>
          </EmptyState.Action>
        </EmptyState>
      </Row>
    </Grid>
  );
};

CredentialsEmptyState.propTypes = {
  onAddCredential: PropTypes.func,
  onAddSource: PropTypes.func
};

export default CredentialsEmptyState;
