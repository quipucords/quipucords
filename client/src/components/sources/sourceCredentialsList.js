import React from 'react';
import PropTypes from 'prop-types';
import { Grid, Icon } from 'patternfly-react';
import _ from 'lodash';

const SourceCredentialsList = ({ source }) => {
  const credentials = [..._.get(source, 'credentials', [])];

  credentials.sort((item1, item2) => item1.name.localeCompare(item2.name));

  return (
    <Grid fluid>
      {credentials.map(item => (
        <Grid.Row key={item.name}>
          <Grid.Col xs={12} sm={4}>
            <span>
              <Icon type="fa" name="id-card" />
              &nbsp; {item.name}
            </span>
          </Grid.Col>
        </Grid.Row>
      ))}
    </Grid>
  );
};

SourceCredentialsList.propTypes = {
  source: PropTypes.object
};

SourceCredentialsList.defaultProps = {
  source: {}
};

export { SourceCredentialsList as default, SourceCredentialsList };
